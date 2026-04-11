import os
import json
import tempfile
import re
from google import genai
from google.genai import types
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import PyPDF2
from werkzeug.utils import secure_filename
from app import db
from app.models import StudyMaterial, GeneratedQuestion, GeneratedMindmap

materials_bp = Blueprint("materials", __name__)


def extract_text_from_pdf(filepath):
    text = ""
    with open(filepath, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    return text


def generate_fallback_data(text, filename):
    """Generate plausible demo questions and mindmap from the PDF text when Gemini quota is exhausted."""
    sentences = [s.strip() for s in re.split(r'[.!?]', text) if len(s.strip()) > 40][:20]
    words = re.findall(r'\b[A-Z][a-z]{3,}\b', text)
    key_terms = list(dict.fromkeys(words))[:12]

    topic_name = os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ').title()

    # Summary: pick first 3 long sentences
    summary_points = [f"• {s.strip()}" for s in sentences[:3]]
    if not summary_points:
        summary_points = [f"• This document covers {topic_name} and related concepts."]
    summary = "\n".join(summary_points)

    # Questions
    questions = []
    for i, sentence in enumerate(sentences[:5]):
        question_words = sentence.split()[:6]
        question_stub = " ".join(question_words)
        questions.append({
            "question": f"What does the material say about: \"{question_stub}...\"?",
            "answer": sentence
        })

    generic = [
        {"question": f"What is the main topic covered in {topic_name}?",
         "answer": f"The document covers {topic_name}, focusing on key concepts and their applications."},
        {"question": "What are the most important concepts to remember?",
         "answer": f"Key concepts include: {', '.join(key_terms[:5]) if key_terms else 'the main subject areas outlined in the document'}."},
        {"question": "How are the topics in this material organized?",
         "answer": "The material is organized logically, starting with foundational concepts and building toward advanced topics."},
        {"question": "What are the practical applications of this content?",
         "answer": "This content can be applied directly in academic settings and real-world problem solving."},
        {"question": "What should you study first when reviewing this material?",
         "answer": f"Start with the core definitions of {key_terms[0] if key_terms else topic_name}, then explore related concepts."},
    ]
    while len(questions) < 5:
        questions.append(generic[len(questions)])

    subtopics = key_terms[:6] if key_terms else ["Concepts", "Methods", "Applications", "Summary"]
    mermaid_lines = ["graph TD", f"  A[{topic_name}]"]
    branch_letters = "BCDEFG"
    for i, term in enumerate(subtopics[:6]):
        letter = branch_letters[i]
        mermaid_lines.append(f"  A --> {letter}[{term}]")

    mindmap = "\n".join(mermaid_lines)

    return {"summary": summary, "questions": questions, "mindmap_mermaid": mindmap}


@materials_bp.route("/upload", methods=["POST"])
@jwt_required()
def upload_material():
    user_id = get_jwt_identity()

    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDFs are supported"}), 400

    filename = secure_filename(file.filename)

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return jsonify({"error": "GEMINI_API_KEY not configured on server"}), 500

    # Save temp and extract
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    text = extract_text_from_pdf(tmp_path)
    os.unlink(tmp_path)

    if not text.strip():
        return jsonify({"error": "Could not extract text from PDF. Make sure it is a text-based PDF (not a scanned image)."}), 400

    text = text[:40000]

    # Save material record
    material = StudyMaterial(user_id=user_id, filename=filename)
    db.session.add(material)
    db.session.commit()

    data = None
    used_fallback = False

    # --- Try real Gemini first ---
    prompt = f"""You are an AI study assistant. Read the following text from a PDF study material and do exactly three things:
1. Write a concise TL;DR summary in 3-5 bullet points covering the most important ideas.
2. Generate exactly 5 important study questions and concise answers based on the material.
3. Generate a valid Mermaid.js flowchart (using 'graph TD') that creates a mindmap summarizing the key topics.
   IMPORTANT: Do NOT use parentheses inside node labels — use only square brackets. Example: A[Topic] --> B[Subtopic]

Respond ONLY with a valid JSON object in this exact format (no markdown, no explanation, no code fences):
{{"summary": "• Point one\n• Point two\n• Point three", "questions": [{{"question": "Question text here?", "answer": "Answer text here."}}], "mindmap_mermaid": "graph TD\\n  A[Main Topic] --> B[Subtopic]"}}

PDF Text:
{text}
"""

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        resp_text = response.text.strip()
        if resp_text.startswith("```json"):
            resp_text = resp_text[7:]
        elif resp_text.startswith("```"):
            resp_text = resp_text[3:]
        if resp_text.endswith("```"):
            resp_text = resp_text[:-3]
        data = json.loads(resp_text.strip())
        print("[Gemini] Successfully generated content with real AI.")
    except Exception as e:
        err_str = str(e)
        print(f"[Gemini Error] {type(e).__name__}: {err_str}")
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
            print("[Gemini] Quota exhausted — using smart text-based fallback data.")
            data = generate_fallback_data(text, filename)
            used_fallback = True
        else:
            return jsonify({
                "message": "Material was uploaded but AI processing failed.",
                "material_id": material.material_id,
                "error": err_str
            }), 200

    # --- Save to DB ---
    try:
        for q in data.get("questions", []):
            gq = GeneratedQuestion(
                material_id=material.material_id,
                question_text=q.get("question", ""),
                suggested_answer=q.get("answer", "")
            )
            db.session.add(gq)

        mindmap_markup = data.get("mindmap_mermaid", "graph TD\n  A[No mindmap generated]")
        mm = GeneratedMindmap(material_id=material.material_id, mermaid_markup=mindmap_markup)
        db.session.add(mm)

        # Save summary directly on material row
        material.summary = data.get("summary", None)
        db.session.commit()
    except Exception as e:
        return jsonify({"message": "AI succeeded but DB save failed.", "error": str(e)}), 500

    return jsonify({
        "message": "Successfully processed material",
        "material_id": material.material_id,
        "ai_used": not used_fallback
    }), 201


@materials_bp.route("/<int:material_id>", methods=["GET"])
@jwt_required()
def get_material(material_id):
    user_id = get_jwt_identity()
    material = StudyMaterial.query.filter_by(material_id=material_id, user_id=user_id).first()
    if not material:
        return jsonify({"error": "Material not found"}), 404
    return jsonify(material.to_dict(include_relations=True)), 200


@materials_bp.route("/", methods=["GET"])
@jwt_required()
def list_materials():
    user_id = get_jwt_identity()
    materials = StudyMaterial.query.filter_by(user_id=user_id).order_by(StudyMaterial.uploaded_at.desc()).all()
    return jsonify([m.to_dict() for m in materials]), 200

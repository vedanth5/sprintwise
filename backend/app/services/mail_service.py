import os
import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class MailService:
    @staticmethod
    def send_otp(email, otp):
        """
        Sends a real OTP email using Gmail SMTP and App Passwords.
        """
        sender_email = os.environ.get("MAIL_USERNAME")
        sender_password = os.environ.get("MAIL_PASSWORD") # Your 16-character App Password
        
        if not sender_email or not sender_password:
            print("⚠️ MAIL_USERNAME or MAIL_PASSWORD not set. Falling back to console log.")
            print(f"🔑 OTP for {email}: {otp}")
            return False

        message = MIMEMultipart("alternative")
        message["Subject"] = f"{otp} is your SprintWise verification code"
        message["From"] = f"SprintWise <{sender_email}>"
        message["To"] = email

        text = f"Your verification code is: {otp}"
        html = f"""
        <html>
          <body style="font-family: sans-serif; color: #333;">
            <div style="max-width: 400px; margin: auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
              <h2 style="color: #8B5CF6;">⚡ SprintWise</h2>
              <p>Welcome! Use the code below to verify your account:</p>
              <div style="font-size: 32px; font-weight: bold; color: #8B5CF6; letter-spacing: 5px; margin: 20px 0;">
                {otp}
              </div>
              <p style="font-size: 12px; color: #999;">This code will expire in 10 minutes.</p>
            </div>
          </body>
        </html>
        """

        message.attach(MIMEText(text, "plain"))
        message.attach(MIMEText(html, "html"))

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, email, message.as_string())
            print(f"✅ Real email sent successfully to {email}")
            return True
        except Exception as e:
            print(f"❌ Failed to send email: {str(e)}")
            return False

    @staticmethod
    def generate_otp():
        return str(random.randint(100000, 999999))

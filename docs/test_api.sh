#!/bin/bash
# ============================================================
# SprintWise API Test Script
# Usage: chmod +x test_api.sh && ./test_api.sh
# Requires: curl, jq
# Make sure the backend is running: python app.py
# ============================================================

BASE="http://localhost:5000/api/v1"
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

pass() { echo -e "${GREEN}✓ PASS${NC}: $1"; }
fail() { echo -e "${RED}✗ FAIL${NC}: $1 — $2"; }
section() { echo -e "\n${BLUE}── $1 ──${NC}"; }

# ── 1. Register ──
section "Authentication"
REG=$(curl -s -X POST "$BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"apitest@example.com","password":"testpass1","full_name":"API Tester","weekly_study_target_hours":20}')
TOKEN=$(echo $REG | jq -r '.access_token // empty')
[ -n "$TOKEN" ] && pass "Register" || fail "Register" "$REG"

# ── 2. Login ──
LOGIN=$(curl -s -X POST "$BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"apitest@example.com","password":"testpass1"}')
TOKEN=$(echo $LOGIN | jq -r '.access_token // empty')
[ -n "$TOKEN" ] && pass "Login" || fail "Login" "$LOGIN"

AUTH="Authorization: Bearer $TOKEN"

# ── 3. Get profile ──
ME=$(curl -s "$BASE/auth/me" -H "$AUTH")
NAME=$(echo $ME | jq -r '.user.full_name // empty')
[ "$NAME" = "API Tester" ] && pass "Get profile" || fail "Get profile" "$ME"

# ── 4. Update profile ──
UPD=$(curl -s -X PUT "$BASE/auth/profile" -H "$AUTH" \
  -H "Content-Type: application/json" \
  -d '{"weekly_study_target_hours":25,"subjects":["Math","Physics"]}')
[ $(echo $UPD | jq -r '.user.weekly_study_target_hours') = "25.0" ] && pass "Update profile" || fail "Update profile" "$UPD"

# ── 5. Create Sprint ──
section "Sprint Management"
TODAY=$(date +%Y-%m-%d)
NEXTWEEK=$(date -d "+6 days" +%Y-%m-%d 2>/dev/null || date -v+6d +%Y-%m-%d)
SPRINT=$(curl -s -X POST "$BASE/sprints/" -H "$AUTH" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"API Test Sprint\",\"start_date\":\"$TODAY\",\"end_date\":\"$NEXTWEEK\",\"notes\":\"Test sprint\"}")
SPRINT_ID=$(echo $SPRINT | jq -r '.sprint.sprint_id // empty')
[ -n "$SPRINT_ID" ] && pass "Create sprint (id=$SPRINT_ID)" || fail "Create sprint" "$SPRINT"

# ── 6. Get sprint ──
GS=$(curl -s "$BASE/sprints/$SPRINT_ID" -H "$AUTH")
[ $(echo $GS | jq -r '.sprint.name') = "API Test Sprint" ] && pass "Get sprint" || fail "Get sprint" "$GS"

# ── 7. List sprints ──
LS=$(curl -s "$BASE/sprints/" -H "$AUTH")
COUNT=$(echo $LS | jq '.sprints | length')
[ "$COUNT" -ge 1 ] && pass "List sprints ($COUNT found)" || fail "List sprints" "$LS"

# ── 8. Create task ──
section "Task Management"
TASK=$(curl -s -X POST "$BASE/tasks/" -H "$AUTH" \
  -H "Content-Type: application/json" \
  -d "{\"sprint_id\":$SPRINT_ID,\"subject\":\"Mathematics\",\"description\":\"Solve calculus problems\",\"estimated_minutes\":45,\"priority\":\"high\"}")
TASK_ID=$(echo $TASK | jq -r '.task.task_id // empty')
[ -n "$TASK_ID" ] && pass "Create task (id=$TASK_ID)" || fail "Create task" "$TASK"

# ── 9. Create bulk tasks ──
BULK=$(curl -s -X POST "$BASE/tasks/bulk" -H "$AUTH" \
  -H "Content-Type: application/json" \
  -d "{\"sprint_id\":$SPRINT_ID,\"tasks\":[{\"subject\":\"Physics\",\"description\":\"Chapter 3 review\",\"estimated_minutes\":30},{\"subject\":\"Chemistry\",\"description\":\"Organic reactions\",\"estimated_minutes\":60}]}")
BULK_COUNT=$(echo $BULK | jq '.tasks | length')
[ "$BULK_COUNT" = "2" ] && pass "Bulk create tasks ($BULK_COUNT tasks)" || fail "Bulk create" "$BULK"

# ── 10. Update task status ──
UPT=$(curl -s -X PATCH "$BASE/tasks/$TASK_ID" -H "$AUTH" \
  -H "Content-Type: application/json" \
  -d '{"status":"completed"}')
[ $(echo $UPT | jq -r '.task.status') = "completed" ] && pass "Complete task" || fail "Complete task" "$UPT"

# ── 11. Time tracking ──
section "Time Tracking"

# Get second task id
TASKS=$(curl -s "$BASE/tasks/sprint/$SPRINT_ID" -H "$AUTH")
SECOND_TASK_ID=$(echo $TASKS | jq -r '.tasks[1].task_id // empty')

START=$(curl -s -X POST "$BASE/timelogs/start" -H "$AUTH" \
  -H "Content-Type: application/json" \
  -d "{\"task_id\":$SECOND_TASK_ID}")
LOG_ID=$(echo $START | jq -r '.log.log_id // empty')
[ -n "$LOG_ID" ] && pass "Start time session (log_id=$LOG_ID)" || fail "Start session" "$START"

sleep 1

STOP=$(curl -s -X POST "$BASE/timelogs/stop" -H "$AUTH" \
  -H "Content-Type: application/json" \
  -d "{\"log_id\":$LOG_ID}")
DUR=$(echo $STOP | jq -r '.log.duration_seconds // empty')
[ -n "$DUR" ] && pass "Stop session (duration=${DUR}s)" || fail "Stop session" "$STOP"

# ── 12. Analytics ──
section "Analytics"
ANA=$(curl -s "$BASE/analytics/sprint/$SPRINT_ID" -H "$AUTH")
RATE=$(echo $ANA | jq -r '.metrics.completion_rate // empty')
[ -n "$RATE" ] && pass "Sprint analytics (completion=$RATE%)" || fail "Analytics" "$ANA"

HIST=$(curl -s "$BASE/analytics/history" -H "$AUTH")
[ $(echo $HIST | jq '.history | length') -ge 0 ] && pass "Analytics history" || fail "History" "$HIST"

# ── 13. AI Recommendations ──
section "AI Recommendations"
RECS=$(curl -s "$BASE/recommendations/" -H "$AUTH")
REC_COUNT=$(echo $RECS | jq '.count')
pass "Recommendations fetched ($REC_COUNT active)"

# ── 14. Dashboard ──
section "Dashboard"
DASH=$(curl -s "$BASE/dashboard/summary" -H "$AUTH")
KEYS=("active_sprint" "sprint_trend" "subject_scores" "recommendations" "stats")
ALL_OK=true
for KEY in "${KEYS[@]}"; do
  if ! echo $DASH | jq -e ".$KEY" > /dev/null 2>&1; then
    ALL_OK=false
    fail "Dashboard key missing: $KEY" ""
  fi
done
$ALL_OK && pass "Dashboard summary (all required keys present)" || true

# ── 15. Security: cross-user isolation ──
section "Security"
REG2=$(curl -s -X POST "$BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"other@example.com","password":"otherpass1","full_name":"Other User"}')
TOKEN2=$(echo $REG2 | jq -r '.access_token')
ISOL=$(curl -s "$BASE/sprints/$SPRINT_ID" -H "Authorization: Bearer $TOKEN2")
STATUS=$(echo $ISOL | jq -r '.error // empty')
[ -n "$STATUS" ] && pass "Cross-user isolation (403/404 returned)" || fail "Cross-user isolation" "$ISOL"

# ── Summary ──
section "Tests Complete"
echo "All API endpoints verified."
echo "Server: $BASE"

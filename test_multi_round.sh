#!/bin/bash
# Test script for progressive multi-turn questioning

API="http://localhost:8000"

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║        Testing Progressive Multi-Turn Questioning Flow          ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Initial request (should get Round 1 questions)
echo "📝 STEP 1: Sending initial request..."
echo "Request: 'i want to design web application'"
echo ""

RESPONSE1=$(curl -s -X POST "$API/api/generate" \
  -H "Content-Type: application/json" \
  -d '{"requirements": "i want to design web application"}')

SESSION_ID=$(echo "$RESPONSE1" | jq -r '.session_id')
ROUND=$(echo "$RESPONSE1" | jq -r '.stage_output.stage_title')
Q_COUNT=$(echo "$RESPONSE1" | jq '.stage_output.questions | length')

echo "✅ Session ID: $SESSION_ID"
echo "✅ Stage: $ROUND"
echo "✅ Question Count: $Q_COUNT"
echo ""
echo "Questions:"
echo "$RESPONSE1" | jq -r '.stage_output.questions[] | "  • \(.question)"' | head -6
echo ""

# Step 2: Answer Round 1 questions (should get Round 2, NOT Stage 2!)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 STEP 2: Answering Round 1 questions..."
echo ""

# Get the first 4 questions
Q1=$(echo "$RESPONSE1" | jq -r '.stage_output.questions[0].question')
Q2=$(echo "$RESPONSE1" | jq -r '.stage_output.questions[1].question')
Q3=$(echo "$RESPONSE1" | jq -r '.stage_output.questions[2].question')
Q4=$(echo "$RESPONSE1" | jq -r '.stage_output.questions[3].question')

# Create answers
ANSWERS=$(cat <<ENDOFJSON
{
  "$Q1": "Web Application",
  "$Q2": "E-commerce platform",
  "$Q3": "1,000–10,000 users",
  "$Q4": "User data"
}
ENDOFJSON
)

echo "Submitting answers..."
RESPONSE2=$(curl -s -X POST "$API/api/stage/approve" \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"stage\": \"stage_1_requirements\",
    \"action\": \"approve\",
    \"answers\": $ANSWERS
  }")

STAGE2=$(echo "$RESPONSE2" | jq -r '.conversation_stage')
ROUND2=$(echo "$RESPONSE2" | jq -r '.stage_output.stage_title')
Q_COUNT2=$(echo "$RESPONSE2" | jq '.stage_output.questions | length')

echo ""
echo "✅ Stage: $STAGE2"
echo "✅ Round: $ROUND2"
echo "✅ Question Count: $Q_COUNT2"
echo ""

if [ "$STAGE2" = "stage_1_requirements" ] && [ "$Q_COUNT2" -gt 0 ]; then
    echo "🎉 SUCCESS: Got Round 2 follow-up questions!"
    echo ""
    echo "Round 2 Questions:"
    echo "$RESPONSE2" | jq -r '.stage_output.questions[] | "  • \(.question)"'
elif [ "$STAGE2" = "stage_2_compute" ]; then
    echo "❌ FAIL: Jumped to Stage 2 (Compute) instead of Round 2!"
    echo ""
    echo "This means the AI decided to stop questioning after Round 1."
    echo "Expected: Round 2 follow-up questions"
    echo "Actual: Moved to Stage 2 Compute recommendations"
else
    echo "⚠️  UNEXPECTED: Stage=$STAGE2, Questions=$Q_COUNT2"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

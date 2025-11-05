#!/usr/bin/env python3
"""
Test script for the auto-fill endpoint.
Simulates a KG session and tests AI-powered auto-fill feature.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"


def test_autofill():
    """Test the complete auto-fill workflow."""
    
    # Step 1: Start a KG session
    print("🚀 Starting Knowledge Graph session...")
    start_response = requests.post(
        f"{BASE_URL}/api/kg/start",
        json={"requirements": "I need an Azure e-commerce platform for 10,000 users with payment processing"}
    )
    
    if start_response.status_code != 200:
        print(f"❌ Failed to start session: {start_response.text}")
        return
    
    start_data = start_response.json()
    print(f"📦 Response data: {json.dumps(start_data, indent=2)}")
    
    session_id = start_data["session_id"]
    current_domain = start_data.get("current_domain") or start_data.get("domain")
    questions = start_data["questions"]
    
    print(f"✅ Session started: {session_id}")
    print(f"📋 Current domain: {current_domain}")
    print(f"📝 Questions count: {len(questions)}")
    print()
    
    # Step 2: Test auto-fill endpoint
    print("🤖 Testing auto-fill endpoint...")
    autofill_response = requests.post(
        f"{BASE_URL}/api/kg/autofill",
        json={
            "session_id": session_id,
            "domain": current_domain,
            "questions": questions
        },
        timeout=120  # 2 minutes timeout
    )
    
    if autofill_response.status_code != 200:
        print(f"❌ Auto-fill failed: {autofill_response.text}")
        return
    
    autofill_data = autofill_response.json()
    suggested_answers = autofill_data.get("suggested_answers", {})
    
    print(f"✅ Auto-fill successful!")
    print(f"📊 Suggested answers count: {len(suggested_answers)}")
    print()
    print("🎯 Suggested Answers:")
    print(json.dumps(suggested_answers, indent=2))
    print()
    
    # Step 3: Verify answers match question fields
    print("🔍 Validating suggested answers...")
    question_fields = {q["field_name"] for q in questions}
    suggested_fields = set(suggested_answers.keys())
    
    matching = question_fields & suggested_fields
    missing = question_fields - suggested_fields
    extra = suggested_fields - question_fields
    
    print(f"✅ Matching fields: {len(matching)}/{len(question_fields)}")
    if missing:
        print(f"⚠️  Missing answers: {missing}")
    if extra:
        print(f"⚠️  Extra answers: {extra}")
    
    # Step 4: Validate answer values
    print()
    print("🔍 Validating answer values against options...")
    valid_count = 0
    invalid_count = 0
    
    for question in questions:
        field_name = question["field_name"]
        suggested_value = suggested_answers.get(field_name)
        
        if suggested_value is None:
            continue
        
        if question.get("options"):
            if suggested_value in question["options"]:
                valid_count += 1
            else:
                invalid_count += 1
                print(f"❌ Invalid answer for {field_name}: '{suggested_value}'")
                print(f"   Valid options: {question['options']}")
        else:
            valid_count += 1  # Free-form input, always valid
    
    print(f"✅ Valid answers: {valid_count}")
    print(f"❌ Invalid answers: {invalid_count}")
    
    if invalid_count == 0:
        print()
        print("🎉 Auto-fill test PASSED!")
    else:
        print()
        print("⚠️  Auto-fill test PARTIAL SUCCESS (some invalid answers)")


if __name__ == "__main__":
    try:
        test_autofill()
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Is the backend server running?")
        print("   Run: cd /Users/robenhai/CoPilot-SE && source .venv/bin/activate && python -m uvicorn api.server:app --reload")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

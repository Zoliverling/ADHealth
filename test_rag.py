import os
import sys
from dotenv import load_dotenv
from rag_system.utils.interface import DiabetesInsightInterface

def test_glucose_insights():
    interface = DiabetesInsightInterface()
    test_cases = [
        {"glucose_level": 200},
        {"glucose_level": 65},
        {"glucose_level": 120}
    ]
    
    print("Testing glucose insights...")
    for case in test_cases:
        insights = interface.get_insights(case)
        print(f"\nInput: Glucose = {case['glucose_level']}")
        print(f"Output: {insights['glucose']}")
        print("-" * 80)

def test_insulin_insights():
    interface = DiabetesInsightInterface()
    test_cases = [
        {"insulin_units": 10, "glucose_level": 180},
        {"insulin_units": 5, "glucose_level": 90},
    ]
    
    print("\nTesting insulin insights...")
    for case in test_cases:
        insights = interface.get_insights(case)
        print(f"\nInput: Insulin = {case['insulin_units']}, Glucose = {case['glucose_level']}")
        print(f"Output: {insights['insulin']}")
        print("-" * 80)

def test_blood_pressure_insights():
    interface = DiabetesInsightInterface()
    test_cases = [
        {"systolic_bp": 140, "diastolic_bp": 90},
        {"systolic_bp": 120, "diastolic_bp": 80},
    ]
    
    print("\nTesting blood pressure insights...")
    for case in test_cases:
        insights = interface.get_insights(case)
        print(f"\nInput: BP = {case['systolic_bp']}/{case['diastolic_bp']}")
        print(f"Output: {insights['blood_pressure']}")
        print("-" * 80)

if __name__ == "__main__":
    load_dotenv()
    
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable is not set")
        sys.exit(1)
    
    print("Starting RAG system tests...\n")
    
    try:
        test_glucose_insights()
        test_insulin_insights()
        test_blood_pressure_insights()
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        sys.exit(1)
    
    print("\nAll tests completed successfully!")
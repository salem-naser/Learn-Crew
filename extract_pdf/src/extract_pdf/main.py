#!/usr/bin/env python
import sys
import warnings
import os
import json
from pathlib import Path

from datetime import datetime

from extract_pdf.crew import ExtractPdf

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew to extract PDF, format to API schema, validate, and POST to API.
    """
    # Get PDF path
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = input("Enter the path to your PDF file: ").strip()
    
    # Validate PDF path
    if not os.path.exists(pdf_path):
        raise Exception(f"PDF file not found: {pdf_path}")
    
    if not pdf_path.lower().endswith('.pdf'):
        raise Exception(f"File must be a PDF: {pdf_path}")
    
    # Get API configuration from environment or prompt
    api_url = os.getenv('API_URL')
    if not api_url:
        api_url = input("Enter API endpoint URL (or press Enter to skip API posting): ").strip()
    
    api_token = os.getenv('API_TOKEN', '')
    
    # Determine schema path
    schema_path = os.path.join(
        os.path.dirname(__file__),
        'config',
        'api_schema.json'
    )
    
    # Verify schema exists
    if not os.path.exists(schema_path):
        print(f"Warning: API schema not found at {schema_path}")
        print("Creating a default schema...")
        # Schema will be created by default in config folder
    
    # Prepare API headers
    api_headers = {
        "Content-Type": "application/json"
    }
    
    if api_token:
        api_headers["Authorization"] = f"Bearer {api_token}"
    
    inputs = {
        'pdf_path': pdf_path,
        'schema_path': schema_path,
        'api_url': api_url if api_url else 'http://localhost:8000/api/users',  # Default placeholder
        'api_headers': json.dumps(api_headers)
    }

    try:
        print("\n" + "="*60)
        print("Starting PDF to JSON to API Workflow")
        print("="*60)
        print(f"PDF File: {pdf_path}")
        print(f"API Schema: {schema_path}")
        print(f"API Endpoint: {inputs['api_url']}")
        print("="*60 + "\n")
        
        result = ExtractPdf().crew().kickoff(inputs=inputs)
        
        print("\n" + "="*60)
        print("✓ Workflow Completed Successfully!")
        print("="*60)
        print(f"✓ Formatted data saved to: formatted_data.json")
        if api_url:
            print(f"✓ API response saved to: api_response.json")
        print("="*60)
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "topic": "AI LLMs",
        'current_year': str(datetime.now().year)
    }
    try:
        ExtractPdf().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        ExtractPdf().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year)
    }

    try:
        ExtractPdf().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

def run_with_trigger():
    """
    Run the crew with trigger payload.
    """
    import json

    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    inputs = {
        "crewai_trigger_payload": trigger_payload,
        "topic": "",
        "current_year": ""
    }

    try:
        result = ExtractPdf().crew().kickoff(inputs=inputs)
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew with trigger: {e}")

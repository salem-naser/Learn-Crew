#!/usr/bin/env python
import sys
import warnings
import os
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
    Run the crew to extract data from PDF and convert to JSON.
    """
    # You can change this to your PDF file path
    # Example: pdf_path = "path/to/your/document.pdf"
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        # Default PDF path - you can change this
        pdf_path = input("Enter the path to your PDF file: ").strip()
    
    # Validate PDF path
    if not os.path.exists(pdf_path):
        raise Exception(f"PDF file not found: {pdf_path}")
    
    if not pdf_path.lower().endswith('.pdf'):
        raise Exception(f"File must be a PDF: {pdf_path}")
    
    inputs = {
        'pdf_path': pdf_path
    }

    try:
        result = ExtractPdf().crew().kickoff(inputs=inputs)
        print("\n" + "="*50)
        print("PDF extraction completed!")
        print("Output saved to: extracted_data.json")
        print("="*50)
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

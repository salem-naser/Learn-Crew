from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import PyPDF2
import json
from pathlib import Path
import requests
from jsonschema import validate, Draft7Validator


class PDFExtractorInput(BaseModel):
    """Input schema for PDFExtractorTool."""
    pdf_path: str = Field(..., description="Path to the PDF file to extract data from.")


class PDFExtractorTool(BaseTool):
    name: str = "PDF Data Extractor"
    description: str = (
        "Extracts text content from PDF files. Useful for reading and analyzing PDF documents. "
        "Returns the extracted text content from all pages of the PDF."
    )
    args_schema: Type[BaseModel] = PDFExtractorInput

    def _run(self, pdf_path: str) -> str:
        """
        Extract text from PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text content from the PDF
        """
        try:
            pdf_file = Path(pdf_path)
            if not pdf_file.exists():
                return f"Error: PDF file not found at {pdf_path}"
            
            if not pdf_file.suffix.lower() == '.pdf':
                return f"Error: File {pdf_path} is not a PDF file"
            
            extracted_text = []
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    extracted_text.append({
                        'page': page_num + 1,
                        'content': text.strip()
                    })
            
            return json.dumps(extracted_text, indent=2)
            
        except Exception as e:
            return f"Error extracting PDF: {str(e)}"


class JSONValidatorInput(BaseModel):
    """Input schema for JSONValidatorTool."""
    json_data: str = Field(..., description="JSON data as string to validate against schema.")
    schema_path: str = Field(..., description="Path to the JSON schema file to validate against.")


class JSONValidatorTool(BaseTool):
    name: str = "JSON Schema Validator"
    description: str = (
        "Validates JSON data against a JSON schema. "
        "Ensures the data structure matches the required API format before sending. "
        "Returns validation result with detailed error messages if validation fails."
    )
    args_schema: Type[BaseModel] = JSONValidatorInput

    def _run(self, json_data: str, schema_path: str) -> str:
        """
        Validate JSON data against a schema.
        
        Args:
            json_data: JSON string to validate
            schema_path: Path to JSON schema file
            
        Returns:
            Validation result message
        """
        try:
            # Parse JSON data
            try:
                data = json.loads(json_data)
            except json.JSONDecodeError as e:
                return f"Invalid JSON format: {str(e)}"
            
            # Load schema
            schema_file = Path(schema_path)
            if not schema_file.exists():
                return f"Schema file not found: {schema_path}"
            
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            
            # Validate
            validator = Draft7Validator(schema)
            errors = list(validator.iter_errors(data))
            
            if errors:
                error_messages = []
                for error in errors:
                    path = '.'.join(str(p) for p in error.path) if error.path else 'root'
                    error_messages.append(f"  - At '{path}': {error.message}")
                
                return f"Validation failed with {len(errors)} error(s):\n" + "\n".join(error_messages)
            
            return "✓ JSON validation successful! Data matches the required schema."
            
        except Exception as e:
            return f"Validation error: {str(e)}"


class APIPostInput(BaseModel):
    """Input schema for APIPostTool."""
    api_url: str = Field(..., description="The API endpoint URL to post data to.")
    json_data: str = Field(..., description="JSON data as string to send to the API.")
    headers: str = Field(default="{}", description="Optional HTTP headers as JSON string.")


class APIPostTool(BaseTool):
    name: str = "API POST Sender"
    description: str = (
        "Sends JSON data to an API endpoint via HTTP POST request. "
        "Use this after validating JSON data to submit it to the target API. "
        "Returns the API response status and message."
    )
    args_schema: Type[BaseModel] = APIPostInput

    def _run(self, api_url: str, json_data: str, headers: str = "{}") -> str:
        """
        Post JSON data to an API endpoint.
        
        Args:
            api_url: Target API endpoint URL
            json_data: JSON data to send
            headers: Optional HTTP headers
            
        Returns:
            API response information
        """
        try:
            # Parse JSON data
            try:
                data = json.loads(json_data)
            except json.JSONDecodeError as e:
                return f"Invalid JSON format: {str(e)}"
            
            # Parse headers
            try:
                request_headers = json.loads(headers)
                # Ensure Content-Type is set
                if 'Content-Type' not in request_headers:
                    request_headers['Content-Type'] = 'application/json'
            except json.JSONDecodeError:
                request_headers = {'Content-Type': 'application/json'}
            
            # Make POST request
            response = requests.post(
                api_url,
                json=data,
                headers=request_headers,
                timeout=30
            )
            
            # Format response
            result = {
                'status_code': response.status_code,
                'success': response.ok,
                'url': api_url,
                'response_body': response.text[:500] if response.text else 'No response body'
            }
            
            if response.ok:
                return f"✓ API POST successful!\n{json.dumps(result, indent=2)}"
            else:
                return f"✗ API POST failed with status {response.status_code}\n{json.dumps(result, indent=2)}"
            
        except requests.exceptions.RequestException as e:
            return f"Network error: {str(e)}"
        except Exception as e:
            return f"Error posting to API: {str(e)}"

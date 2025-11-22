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


class FDALookupInput(BaseModel):
    """Input schema for FDALookupTool."""
    medication_name: str = Field(..., description="Name of the medication to lookup in FDA database.")
    brand_name: str = Field(default="", description="Optional brand name of the medication.")


class FDALookupTool(BaseTool):
    name: str = "FDA Medication Lookup"
    description: str = (
        "Looks up medication information from FDA openFDA API. "
        "Use this to fill missing medication data like dosage, strength, form, route, "
        "generic name, manufacturer, and warnings. Searches by medication name or brand name."
    )
    args_schema: Type[BaseModel] = FDALookupInput

    def _run(self, medication_name: str, brand_name: str = "") -> str:
        """
        Query FDA openFDA API for medication information.
        
        Args:
            medication_name: Name of the medication (generic or brand)
            brand_name: Optional brand name for more specific search
            
        Returns:
            Medication information from FDA database
        """
        try:
            # Load FDA API config
            import os
            config_path = Path(__file__).parent.parent / 'config' / 'api_config.json'
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Get FDA API base URL from config
            fda_config = config['external_apis']['fda_drug_label']
            base_url = fda_config['base_url']
            
            # Build search query
            search_name = brand_name if brand_name else medication_name
            query = f'openfda.brand_name:"{search_name}" OR openfda.generic_name:"{search_name}"'
            
            params = {
                'search': query,
                'limit': 1
            }
            
            response = requests.get(base_url, params=params, timeout=10)
            
            if response.status_code != 200:
                return f"FDA API returned status {response.status_code}. Medication data may not be available."
            
            data = response.json()
            
            if 'results' not in data or len(data['results']) == 0:
                return f"No FDA data found for medication: {medication_name}"
            
            result = data['results'][0]
            openfda = result.get('openfda', {})
            
            # Extract relevant medication information
            medication_info = {
                'found': True,
                'generic_name': openfda.get('generic_name', [None])[0],
                'brand_name': openfda.get('brand_name', [None])[0],
                'manufacturer': openfda.get('manufacturer_name', [None])[0],
                'product_type': openfda.get('product_type', [None])[0],
                'route': openfda.get('route', []),
                'dosage_form': openfda.get('dosage_form', [None])[0],
                'strength': openfda.get('substance_name', []),
                'ndc': openfda.get('product_ndc', [None])[0],
                'drug_class': openfda.get('pharm_class_epc', []),
                'warnings': result.get('warnings', []),
                'indications': result.get('indications_and_usage', []),
                'dosage_and_administration': result.get('dosage_and_administration', []),
                'adverse_reactions': result.get('adverse_reactions', []),
                'drug_interactions': result.get('drug_interactions', [])
            }
            
            return json.dumps(medication_info, indent=2)
            
        except requests.exceptions.RequestException as e:
            return f"FDA API network error: {str(e)}"
        except Exception as e:
            return f"Error querying FDA database: {str(e)}"


class GUIDExtractorInput(BaseModel):
    """Input schema for GUIDExtractorTool."""
    api_response: str = Field(..., description="API response JSON as string containing user GUID.")
    guid_field: str = Field(default="user_guid", description="Field name containing the GUID in response.")


class GUIDExtractorTool(BaseTool):
    name: str = "GUID Extractor"
    description: str = (
        "Extracts user GUID from API response. "
        "Use this after posting user data to extract the GUID needed for medication endpoint. "
        "Returns the extracted GUID value."
    )
    args_schema: Type[BaseModel] = GUIDExtractorInput

    def _run(self, api_response: str, guid_field: str = "user_guid") -> str:
        """
        Extract GUID from API response.
        
        Args:
            api_response: API response JSON string
            guid_field: Name of the field containing GUID
            
        Returns:
            Extracted GUID value
        """
        try:
            # Parse response
            try:
                response_data = json.loads(api_response)
            except json.JSONDecodeError as e:
                return f"Invalid JSON response format: {str(e)}"
            
            # Extract GUID
            guid = None
            
            # Check direct field
            if guid_field in response_data:
                guid = response_data[guid_field]
            # Check in response_body
            elif 'response_body' in response_data:
                try:
                    body = json.loads(response_data['response_body'])
                    if guid_field in body:
                        guid = body[guid_field]
                except:
                    pass
            # Check nested structures
            elif 'data' in response_data and guid_field in response_data['data']:
                guid = response_data['data'][guid_field]
            
            if not guid:
                return f"GUID field '{guid_field}' not found in API response. Available fields: {list(response_data.keys())}"
            
            # Validate GUID format
            import re
            guid_pattern = r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
            if not re.match(guid_pattern, str(guid)):
                return f"Warning: Extracted value '{guid}' does not match GUID format, but returning it anyway."
            
            return f"✓ GUID extracted successfully: {guid}"
            
        except Exception as e:
            return f"Error extracting GUID: {str(e)}"

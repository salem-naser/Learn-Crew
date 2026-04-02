from crewai.tools import BaseTool
from typing import Type, Optional
from pydantic import BaseModel, Field
import PyPDF2
import json
from pathlib import Path
import requests
from jsonschema import validate, Draft7Validator
import time

# Import logging and database utilities
from extract_pdf.logging_config import get_logger, log_task_event
from extract_pdf.db_logger import get_db_logger

# Loggers for different components
logger = get_logger('main')
validation_logger = get_logger('validation')
api_logger = get_logger('api')


# Context holder for workflow tracking
class WorkflowContext:
    """Holds the current workflow run_id for logging purposes."""
    run_id: Optional[str] = None
    
    @classmethod
    def set_run_id(cls, run_id: str):
        cls.run_id = run_id
    
    @classmethod
    def get_run_id(cls) -> Optional[str]:
        return cls.run_id


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
        start_time = time.time()
        logger.info(f"Starting PDF extraction: {pdf_path}")
        
        try:
            pdf_file = Path(pdf_path)
            if not pdf_file.exists():
                logger.error(f"PDF file not found: {pdf_path}")
                return f"Error: PDF file not found at {pdf_path}"
            
            if not pdf_file.suffix.lower() == '.pdf':
                logger.error(f"Invalid file type: {pdf_path}")
                return f"Error: File {pdf_path} is not a PDF file"
            
            extracted_text = []
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                logger.info(f"Processing {num_pages} pages from PDF")
                
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    extracted_text.append({
                        'page': page_num + 1,
                        'content': text.strip()
                    })
            
            duration = time.time() - start_time
            logger.info(f"PDF extraction completed: {num_pages} pages in {duration:.2f}s")
            
            # Log to database if workflow context exists
            if WorkflowContext.get_run_id():
                db = get_db_logger()
                db.log_task_execution(
                    run_id=WorkflowContext.get_run_id(),
                    task_name='pdf_extraction',
                    status='completed',
                    input_summary=f"PDF: {pdf_path}",
                    output_summary=f"Extracted {num_pages} pages",
                    duration=duration
                )
            
            return json.dumps(extracted_text, indent=2)
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"PDF extraction failed: {str(e)}")
            
            if WorkflowContext.get_run_id():
                db = get_db_logger()
                db.log_task_execution(
                    run_id=WorkflowContext.get_run_id(),
                    task_name='pdf_extraction',
                    status='failed',
                    error_message=str(e),
                    duration=duration
                )
            
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
        start_time = time.time()
        schema_name = Path(schema_path).stem
        validation_logger.info(f"Starting JSON validation against: {schema_name}")
        
        try:
            # Parse JSON data
            try:
                data = json.loads(json_data)
            except json.JSONDecodeError as e:
                validation_logger.error(f"Invalid JSON format: {e}")
                return f"Invalid JSON format: {str(e)}"
            
            # Load schema
            schema_file = Path(schema_path)
            if not schema_file.exists():
                validation_logger.error(f"Schema file not found: {schema_path}")
                return f"Schema file not found: {schema_path}"
            
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            
            # Validate
            validator = Draft7Validator(schema)
            errors = list(validator.iter_errors(data))
            
            duration = time.time() - start_time
            
            if errors:
                error_messages = []
                for error in errors:
                    path = '.'.join(str(p) for p in error.path) if error.path else 'root'
                    error_messages.append(f"  - At '{path}': {error.message}")
                
                validation_logger.warning(f"Validation failed: {len(errors)} errors in {schema_name}")
                
                # Log to database
                if WorkflowContext.get_run_id():
                    db = get_db_logger()
                    db.log_validation(
                        run_id=WorkflowContext.get_run_id(),
                        task_name='json_validation',
                        validator_type='jsonschema',
                        schema_name=schema_name,
                        is_valid=False,
                        errors=error_messages,
                        raw_input=json_data[:2000]
                    )
                
                return f"Validation failed with {len(errors)} error(s):\n" + "\n".join(error_messages)
            
            validation_logger.info(f"Validation successful: {schema_name} in {duration:.2f}s")
            
            # Log to database
            if WorkflowContext.get_run_id():
                db = get_db_logger()
                db.log_validation(
                    run_id=WorkflowContext.get_run_id(),
                    task_name='json_validation',
                    validator_type='jsonschema',
                    schema_name=schema_name,
                    is_valid=True,
                    raw_input=json_data[:2000]
                )
            
            return "✓ JSON validation successful! Data matches the required schema."
            
        except Exception as e:
            validation_logger.error(f"Validation error: {e}")
            return f"Validation error: {str(e)}"


class APIPostInput(BaseModel):
    """Input schema for APIPostTool."""
    api_url: str = Field(..., description="The API endpoint URL to post data to.")
    json_data: str = Field(..., description="JSON data as string to send to the API.")
    headers: str = Field(default="{}", description="Optional HTTP headers as JSON string.")
    endpoint_name: str = Field(default="api", description="Name of the endpoint for logging (user_endpoint, medication_endpoint)")


class APIPostTool(BaseTool):
    name: str = "API POST Sender"
    description: str = (
        "Sends JSON data to an API endpoint via HTTP POST request. "
        "Use this after validating JSON data to submit it to the target API. "
        "Returns the API response status and message."
    )
    args_schema: Type[BaseModel] = APIPostInput

    def _run(self, api_url: str, json_data: str, headers: str = "{}", endpoint_name: str = "api") -> str:
        """
        Post JSON data to an API endpoint.
        
        Args:
            api_url: Target API endpoint URL
            json_data: JSON data to send
            headers: Optional HTTP headers
            endpoint_name: Name of the endpoint for logging
            
        Returns:
            API response information
        """
        start_time = time.time()
        api_logger.info(f"Starting API POST to: {endpoint_name} ({api_url})")
        
        try:
            # Parse JSON data
            try:
                data = json.loads(json_data)
            except json.JSONDecodeError as e:
                api_logger.error(f"Invalid JSON format for API call: {e}")
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
            
            response_time = time.time() - start_time
            
            # Format response
            result = {
                'status_code': response.status_code,
                'success': response.ok,
                'url': api_url,
                'response_body': response.text[:500] if response.text else 'No response body'
            }
            
            # Log to database
            if WorkflowContext.get_run_id():
                db = get_db_logger()
                db.log_api_call(
                    run_id=WorkflowContext.get_run_id(),
                    endpoint_name=endpoint_name,
                    url=api_url,
                    method='POST',
                    response_code=response.status_code,
                    response_time=response_time,
                    is_success=response.ok,
                    request_summary=json_data[:500],
                    response_summary=response.text[:500] if response.text else None
                )
            
            if response.ok:
                api_logger.info(f"API POST successful: {endpoint_name} -> {response.status_code} in {response_time:.2f}s")
                return f"✓ API POST successful!\n{json.dumps(result, indent=2)}"
            else:
                api_logger.warning(f"API POST failed: {endpoint_name} -> {response.status_code}")
                return f"✗ API POST failed with status {response.status_code}\n{json.dumps(result, indent=2)}"
            
        except requests.exceptions.RequestException as e:
            response_time = time.time() - start_time
            api_logger.error(f"Network error on {endpoint_name}: {e}")
            
            if WorkflowContext.get_run_id():
                db = get_db_logger()
                db.log_api_call(
                    run_id=WorkflowContext.get_run_id(),
                    endpoint_name=endpoint_name,
                    url=api_url,
                    method='POST',
                    response_time=response_time,
                    is_success=False,
                    error_message=str(e)
                )
            
            return f"Network error: {str(e)}"
        except Exception as e:
            api_logger.error(f"Error posting to API: {e}")
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
        logger.info(f"Extracting GUID from API response, field: {guid_field}")
        
        try:
            # Parse response
            try:
                response_data = json.loads(api_response)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON response format: {e}")
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
                logger.warning(f"GUID field '{guid_field}' not found in response")
                return f"GUID field '{guid_field}' not found in API response. Available fields: {list(response_data.keys())}"
            
            # Validate GUID format
            import re
            guid_pattern = r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
            if not re.match(guid_pattern, str(guid)):
                logger.warning(f"Extracted value '{guid}' does not match GUID format")
                return f"Warning: Extracted value '{guid}' does not match GUID format, but returning it anyway."
            
            logger.info(f"GUID extracted successfully: {guid}")
            
            # Update workflow with user_guid
            if WorkflowContext.get_run_id():
                db = get_db_logger()
                db.update_workflow_status(
                    run_id=WorkflowContext.get_run_id(),
                    status='running',
                    user_guid=guid
                )
            
            return f"✓ GUID extracted successfully: {guid}"
            
        except Exception as e:
            logger.error(f"Error extracting GUID: {e}")
            return f"Error extracting GUID: {str(e)}"


# =======================
# Guardrails Validator Tool
# =======================

class GuardrailsValidatorInput(BaseModel):
    """Input schema for GuardrailsValidatorTool."""
    json_data: str = Field(..., description="JSON data as string to validate.")
    schema_type: str = Field(..., description="Type of schema to validate against: 'user' or 'medication'")
    auto_correct: bool = Field(default=True, description="Whether to apply auto-corrections to invalid data")


class GuardrailsValidatorTool(BaseTool):
    name: str = "Guardrails Data Validator"
    description: str = (
        "Validates and auto-corrects JSON data using Guardrails framework. "
        "Provides intelligent validation with automatic corrections for common issues "
        "like phone number formatting, date normalization, medication form/route standardization. "
        "Use 'user' schema_type for user data or 'medication' for medication data. "
        "Returns validated (and optionally corrected) data."
    )
    args_schema: Type[BaseModel] = GuardrailsValidatorInput

    def _run(self, json_data: str, schema_type: str, auto_correct: bool = True) -> str:
        """
        Validate and optionally auto-correct JSON data using Guardrails.
        
        Args:
            json_data: JSON string to validate
            schema_type: 'user' or 'medication'
            auto_correct: Whether to apply auto-corrections
            
        Returns:
            Validation result with corrected data if applicable
        """
        start_time = time.time()
        validation_logger.info(f"Starting Guardrails validation for: {schema_type}")
        
        try:
            # Parse JSON data
            try:
                data = json.loads(json_data)
            except json.JSONDecodeError as e:
                validation_logger.error(f"Invalid JSON format: {e}")
                return f"Invalid JSON format: {str(e)}"
            
            # Import guardrails specs
            from extract_pdf.config.guardrails_specs import UserDataGuard, MedicationDataGuard
            
            errors = []
            warnings = []
            corrections = {}
            validated_data = None
            
            try:
                if schema_type.lower() == 'user':
                    guard_model = UserDataGuard
                elif schema_type.lower() == 'medication':
                    guard_model = MedicationDataGuard
                else:
                    return f"Unknown schema_type: {schema_type}. Use 'user' or 'medication'"
                
                # Validate using Pydantic model (Guardrails-style validation)
                validated = guard_model.model_validate(data)
                validated_data = validated.model_dump(mode='json')
                
                # Check for corrections made
                original_json = json.dumps(data, sort_keys=True)
                corrected_json = json.dumps(validated_data, sort_keys=True)
                
                if original_json != corrected_json:
                    # Find what was corrected
                    corrections = self._find_corrections(data, validated_data)
                    for field, (old_val, new_val) in corrections.items():
                        warnings.append(f"Auto-corrected '{field}': '{old_val}' -> '{new_val}'")
                    validation_logger.info(f"Applied {len(corrections)} auto-corrections")
                
            except Exception as e:
                errors.append(str(e))
                validation_logger.warning(f"Guardrails validation failed: {e}")
            
            duration = time.time() - start_time
            is_valid = len(errors) == 0
            
            # Log to database
            if WorkflowContext.get_run_id():
                db = get_db_logger()
                db.log_validation(
                    run_id=WorkflowContext.get_run_id(),
                    task_name='guardrails_validation',
                    validator_type='guardrails',
                    schema_name=schema_type,
                    is_valid=is_valid,
                    errors=errors if errors else None,
                    warnings=warnings if warnings else None,
                    corrections=corrections if corrections else None,
                    raw_input=json_data[:2000],
                    corrected_output=json.dumps(validated_data)[:2000] if validated_data else None
                )
            
            # Build result
            result = {
                'valid': is_valid,
                'schema_type': schema_type,
                'duration': f"{duration:.2f}s"
            }
            
            if errors:
                result['errors'] = errors
                validation_logger.warning(f"Guardrails validation failed: {len(errors)} errors")
                return f"✗ Guardrails validation failed:\n{json.dumps(result, indent=2)}"
            
            if warnings:
                result['corrections_applied'] = len(corrections)
                result['warnings'] = warnings
            
            if auto_correct and validated_data:
                result['corrected_data'] = validated_data
                validation_logger.info(f"Guardrails validation successful with {len(corrections)} corrections")
                return f"✓ Guardrails validation successful!\n{json.dumps(result, indent=2)}"
            
            validation_logger.info(f"Guardrails validation successful in {duration:.2f}s")
            return f"✓ Guardrails validation successful! Data is valid.\n{json.dumps(result, indent=2)}"
            
        except Exception as e:
            validation_logger.error(f"Guardrails validation error: {e}")
            return f"Guardrails validation error: {str(e)}"
    
    def _find_corrections(self, original: dict, corrected: dict, prefix: str = "") -> dict:
        """Find differences between original and corrected data."""
        corrections = {}
        
        for key in set(list(original.keys()) + list(corrected.keys())):
            full_key = f"{prefix}.{key}" if prefix else key
            
            orig_val = original.get(key)
            corr_val = corrected.get(key)
            
            if isinstance(orig_val, dict) and isinstance(corr_val, dict):
                corrections.update(self._find_corrections(orig_val, corr_val, full_key))
            elif isinstance(orig_val, list) and isinstance(corr_val, list):
                for i, (o, c) in enumerate(zip(orig_val, corr_val)):
                    if isinstance(o, dict) and isinstance(c, dict):
                        corrections.update(self._find_corrections(o, c, f"{full_key}[{i}]"))
                    elif o != c:
                        corrections[f"{full_key}[{i}]"] = (o, c)
            elif orig_val != corr_val:
                corrections[full_key] = (orig_val, corr_val)
        
        return corrections

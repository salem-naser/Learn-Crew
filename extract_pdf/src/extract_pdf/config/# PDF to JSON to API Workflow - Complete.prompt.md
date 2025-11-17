# PDF to JSON to API Workflow - Complete Implementation Plan

## Overview
Extract data from PDF files, structure it to match API schema, validate the format, and POST to API endpoint for user information and history data.

## Workflow Architecture

```
PDF File → Extract Tool → Raw Text → Structure Tool → Formatted JSON → Validate Tool → Valid JSON → API POST Tool → API Response
```

## Required Tools

### 1. PDF Extractor Tool (✓ Implemented)
**File**: `src/extract_pdf/tools/custom_tool.py`

```python
class PDFExtractorTool(BaseTool):
    name: str = "PDF Data Extractor"
    description: str = "Extracts text content from PDF files"
    
    def _run(self, pdf_path: str) -> str:
        # Extracts text page by page
        # Returns JSON with page numbers and content
```

### 2. JSON Schema Validator Tool (NEW)
**Purpose**: Validate JSON against API schema before sending

```python
class JSONValidatorInput(BaseModel):
    json_data: str = Field(..., description="JSON data to validate")
    schema_path: str = Field(..., description="Path to JSON schema file")

class JSONValidatorTool(BaseTool):
    name: str = "JSON Schema Validator"
    description: str = (
        "Validates JSON data against a JSON schema. "
        "Ensures data matches required API format before sending."
    )
    
    def _run(self, json_data: str, schema_path: str) -> str:
        # Parse JSON data
        data = json.loads(json_data)
        
        # Load schema from file
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        # Validate using jsonschema
        from jsonschema import validate, Draft7Validator
        validator = Draft7Validator(schema)
        errors = list(validator.iter_errors(data))
        
        if errors:
            return f"Validation failed: {errors}"
        return "✓ Validation successful!"
```

### 3. API POST Tool (NEW)
**Purpose**: Send validated JSON to API endpoint

```python
class APIPostInput(BaseModel):
    api_url: str = Field(..., description="API endpoint URL")
    json_data: str = Field(..., description="JSON data to send")
    headers: str = Field(default="{}", description="HTTP headers as JSON string")

class APIPostTool(BaseTool):
    name: str = "API POST Sender"
    description: str = (
        "Sends JSON data to API endpoint via HTTP POST. "
        "Use after validating JSON to submit to target API."
    )
    
    def _run(self, api_url: str, json_data: str, headers: str = "{}") -> str:
        import requests
        
        # Parse data and headers
        data = json.loads(json_data)
        request_headers = json.loads(headers)
        request_headers['Content-Type'] = 'application/json'
        
        # POST request
        response = requests.post(
            api_url,
            json=data,
            headers=request_headers,
            timeout=30
        )
        
        return {
            'status_code': response.status_code,
            'success': response.ok,
            'response': response.text[:500]
        }
```

## Agent Configuration

### Agent 1: PDF Extractor Agent (✓ Exists)
**File**: `config/agents.yaml`

```yaml
pdf_extractor:
  role: PDF Data Extraction Specialist
  goal: Extract and identify all user information and history data from PDF
  backstory: >
    Expert in reading PDF documents and identifying key data points
    like user information, dates, transactions, and historical records.
  tools:
    - PDFExtractorTool
```

### Agent 2: Data Mapping Specialist (UPDATE EXISTING)
**File**: `config/agents.yaml`

```yaml
data_mapping_specialist:
  role: API Data Mapping and Formatting Specialist
  goal: >
    Transform extracted PDF data into exact API schema format for
    user information and user history data
  backstory: >
    Expert in API integration and data transformation. You understand
    JSON schemas and can map extracted data to match exact API requirements.
    You ensure all required fields are present and correctly formatted
    including user profiles, contact info, and historical transaction data.
```

### Agent 3: API Integration Agent (NEW)
**File**: `config/agents.yaml`

```yaml
api_integration_agent:
  role: API Validation and Integration Specialist
  goal: >
    Validate JSON format against schema and successfully POST data to API
  backstory: >
    You're an expert in API integration and data validation. You ensure
    data matches the required schema before sending, handle API authentication,
    and verify successful data submission. You can troubleshoot API errors
    and ensure data integrity.
  tools:
    - JSONValidatorTool
    - APIPostTool
```

## Task Configuration

### Task 1: Extract PDF Data (✓ Exists)
**File**: `config/tasks.yaml`

```yaml
extract_pdf_task:
  description: >
    Extract all text and data from PDF at {pdf_path}.
    Focus on identifying:
    - User personal information (name, email, phone, address, etc.)
    - User history data (transactions, dates, amounts, statuses, etc.)
    - Any metadata or additional relevant information
  expected_output: >
    Complete extracted text organized by page with all user information
    and historical data clearly identified.
  agent: pdf_extractor
```

### Task 2: Map to API Schema (UPDATE EXISTING)
**File**: `config/tasks.yaml`

```yaml
map_to_api_schema_task:
  description: >
    Transform the extracted PDF data into JSON format matching the API schema at {schema_path}.
    
    Create a JSON object with two main sections:
    1. user_information: Personal details, contact info, demographic data
    2. user_history: Historical records, transactions, activities with dates
    
    Ensure all required fields from the schema are included.
    Use appropriate data types (strings, numbers, dates, arrays, objects).
    Handle missing data gracefully with null or default values as per schema.
  expected_output: >
    Valid JSON matching the API schema with user_information and user_history
    sections properly structured. Return only the JSON without markdown code blocks.
  agent: data_mapping_specialist
  output_file: 'formatted_data.json'
```

### Task 3: Validate JSON Schema (NEW)
**File**: `config/tasks.yaml`

```yaml
validate_json_task:
  description: >
    Validate the formatted JSON data against the API schema at {schema_path}.
    Use the JSON Schema Validator tool to ensure:
    - All required fields are present
    - Data types match schema definitions
    - Format constraints are satisfied (email format, date format, etc.)
    - Nested objects are properly structured
    
    If validation fails, report specific errors with field paths.
  expected_output: >
    Validation result confirming JSON matches schema or detailed error messages
    indicating what needs to be corrected.
  agent: api_integration_agent
  context:
    - map_to_api_schema_task
```

### Task 4: POST to API (NEW)
**File**: `config/tasks.yaml`

```yaml
post_to_api_task:
  description: >
    Send the validated JSON data to the API endpoint at {api_url}.
    
    Use the API POST Sender tool with:
    - URL: {api_url}
    - Headers: {api_headers} (include authentication token if required)
    - JSON data: The validated formatted data
    
    Monitor the response and confirm successful submission.
  expected_output: >
    API response status, success confirmation, and any response data
    from the API including record IDs or confirmation messages.
  agent: api_integration_agent
  context:
    - validate_json_task
```

## JSON Schema Template

### Create API Schema File
**File**: `config/api_schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["user_information", "user_history"],
  "properties": {
    "user_information": {
      "type": "object",
      "required": ["user_id", "full_name", "email"],
      "properties": {
        "user_id": {
          "type": "string",
          "description": "Unique user identifier"
        },
        "full_name": {
          "type": "string",
          "description": "User's full name"
        },
        "email": {
          "type": "string",
          "format": "email",
          "description": "User's email address"
        },
        "phone": {
          "type": "string",
          "description": "Phone number"
        },
        "address": {
          "type": "object",
          "properties": {
            "street": {"type": "string"},
            "city": {"type": "string"},
            "state": {"type": "string"},
            "zip_code": {"type": "string"},
            "country": {"type": "string"}
          }
        },
        "date_of_birth": {
          "type": "string",
          "format": "date",
          "description": "Birth date in YYYY-MM-DD format"
        },
        "registration_date": {
          "type": "string",
          "format": "date-time",
          "description": "Account registration timestamp"
        }
      }
    },
    "user_history": {
      "type": "array",
      "description": "Array of historical records",
      "items": {
        "type": "object",
        "required": ["record_id", "date", "type"],
        "properties": {
          "record_id": {
            "type": "string",
            "description": "Unique record identifier"
          },
          "date": {
            "type": "string",
            "format": "date-time",
            "description": "Record timestamp"
          },
          "type": {
            "type": "string",
            "enum": ["transaction", "activity", "update", "purchase"],
            "description": "Type of historical record"
          },
          "amount": {
            "type": "number",
            "description": "Transaction amount if applicable"
          },
          "status": {
            "type": "string",
            "enum": ["completed", "pending", "failed", "cancelled"],
            "description": "Record status"
          },
          "description": {
            "type": "string",
            "description": "Record description or notes"
          },
          "metadata": {
            "type": "object",
            "description": "Additional record metadata"
          }
        }
      }
    }
  }
}
```

## Updated Dependencies

### Update pyproject.toml

```toml
dependencies = [
    "crewai[tools]==1.4.1",
    "PyPDF2>=3.0.0",
    "requests>=2.31.0",
    "jsonschema>=4.20.0"
]
```

## Updated Crew Configuration

### Update crew.py

```python
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from extract_pdf.tools.custom_tool import (
    PDFExtractorTool,
    JSONValidatorTool,
    APIPostTool
)

@CrewBase
class ExtractPdf():
    """ExtractPdf crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def pdf_extractor(self) -> Agent:
        return Agent(
            config=self.agents_config['pdf_extractor'],
            verbose=True,
            tools=[PDFExtractorTool()]
        )

    @agent
    def data_mapping_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config['data_mapping_specialist'],
            verbose=True
        )

    @agent
    def api_integration_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['api_integration_agent'],
            verbose=True,
            tools=[JSONValidatorTool(), APIPostTool()]
        )

    @task
    def extract_pdf_task(self) -> Task:
        return Task(
            config=self.tasks_config['extract_pdf_task'],
        )

    @task
    def map_to_api_schema_task(self) -> Task:
        return Task(
            config=self.tasks_config['map_to_api_schema_task'],
            output_file='formatted_data.json'
        )

    @task
    def validate_json_task(self) -> Task:
        return Task(
            config=self.tasks_config['validate_json_task'],
        )

    @task
    def post_to_api_task(self) -> Task:
        return Task(
            config=self.tasks_config['post_to_api_task'],
            output_file='api_response.json'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the ExtractPdf crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
```

## Updated Main Entry Point

### Update main.py

```python
#!/usr/bin/env python
import sys
import os
from pathlib import Path
from extract_pdf.crew import ExtractPdf

def run():
    """
    Run the crew to extract PDF, format to API schema, and POST to API.
    """
    # Get PDF path
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = input("Enter the path to your PDF file: ").strip()
    
    # Validate PDF
    if not os.path.exists(pdf_path):
        raise Exception(f"PDF file not found: {pdf_path}")
    
    if not pdf_path.lower().endswith('.pdf'):
        raise Exception(f"File must be a PDF: {pdf_path}")
    
    # Get API configuration
    api_url = os.getenv('API_URL') or input("Enter API endpoint URL: ").strip()
    api_token = os.getenv('API_TOKEN', '')
    
    # Schema path (adjust as needed)
    schema_path = os.path.join(
        os.path.dirname(__file__),
        'config',
        'api_schema.json'
    )
    
    # Prepare API headers
    api_headers = {
        "Authorization": f"Bearer {api_token}" if api_token else "",
        "Content-Type": "application/json"
    }
    
    inputs = {
        'pdf_path': pdf_path,
        'schema_path': schema_path,
        'api_url': api_url,
        'api_headers': json.dumps(api_headers)
    }

    try:
        result = ExtractPdf().crew().kickoff(inputs=inputs)
        print("\n" + "="*50)
        print("✓ PDF extraction and API submission completed!")
        print(f"✓ Formatted data saved to: formatted_data.json")
        print(f"✓ API response saved to: api_response.json")
        print("="*50)
        return result
    except Exception as e:
        raise Exception(f"An error occurred: {e}")
```

## Environment Variables

### Update .env file

```bash
# OpenAI API Key - Required for CrewAI
OPENAI_API_KEY=sk-your-openai-key-here

# Target API Configuration
API_URL=https://api.example.com/users/submit
API_TOKEN=your-api-bearer-token-here

# Optional: API timeout
API_TIMEOUT=30
```

## Installation Commands

```powershell
# Install dependencies
pip install PyPDF2 requests jsonschema

# Or use crewai install
crewai install
```

## Usage Examples

### Example 1: Basic Usage
```powershell
crewai run "c:\documents\user_data.pdf"
```

### Example 2: With Environment Variables
```powershell
# Set in .env file
API_URL=https://api.example.com/users
API_TOKEN=abc123xyz

# Run
crewai run "c:\documents\user_data.pdf"
```

### Example 3: Test Mode (No API POST)
Comment out the `post_to_api_task` in crew configuration to test extraction and validation only.

## Output Files

1. **formatted_data.json** - Validated JSON matching API schema
2. **api_response.json** - Response from API after POST
3. **extracted_data.json** - (Optional) Raw extracted PDF text

## Error Handling

### Common Scenarios

1. **PDF Extraction Fails**
   - Check PDF file format and permissions
   - Ensure PDF contains extractable text (not scanned images)

2. **JSON Validation Fails**
   - Review schema requirements
   - Check for missing required fields
   - Verify data types match schema

3. **API POST Fails**
   - Verify API URL is correct
   - Check authentication token
   - Review API response for error messages
   - Ensure network connectivity

## Testing Strategy

### Phase 1: Test PDF Extraction
- Run only extract_pdf_task
- Verify text extraction quality

### Phase 2: Test JSON Formatting
- Run extract + map_to_api_schema_task
- Validate JSON structure manually

### Phase 3: Test Validation
- Run with validate_json_task
- Confirm schema compliance

### Phase 4: Test API Integration
- Use a test API endpoint first
- Verify successful POST
- Check API response

## Customization Points

### Adjust for Your API Schema
1. Edit `config/api_schema.json` to match your actual API requirements
2. Update field names and types
3. Add/remove required fields
4. Adjust validation rules

### Custom Data Mapping
- Modify `data_mapping_specialist` agent instructions
- Add specific field mapping rules
- Handle domain-specific data formats

### API Authentication
- Update headers in main.py for your auth method
- Support for API keys, OAuth, JWT, etc.

## Next Steps

1. ✅ Review and customize the API schema
2. ✅ Set up environment variables
3. ✅ Install dependencies
4. ✅ Test with sample PDF
5. ✅ Validate JSON output
6. ✅ Test API connection
7. ✅ Run full workflow
8. ✅ Handle edge cases

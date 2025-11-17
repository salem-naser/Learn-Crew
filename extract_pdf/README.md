# PDF to JSON API Extractor - CrewAI Project

Welcome to the PDF to JSON API Extractor, powered by [crewAI](https://crewai.com). This project uses a multi-agent AI system to extract data from PDF files, structure it into JSON format matching your API schema, validate the data, and automatically POST it to your API endpoint.

## What This Project Does

This CrewAI system automates the complete workflow of:
1. **Extracting** text and data from PDF documents
2. **Structuring** the data into JSON format that matches your API schema
3. **Validating** the JSON against the schema to ensure correctness
4. **Posting** the validated data to your API endpoint

Perfect for processing documents containing user information and user history data that need to be submitted to backend systems.

## Installation

Ensure you have Python >=3.10 <3.14 installed on your system.

### Step 1: Install Dependencies

```bash
pip install uv
```

Navigate to your project directory and install all dependencies:

```bash
crewai install
```

Or manually install required packages:

```bash
pip install PyPDF2 requests jsonschema
```

### Step 2: Configure Environment Variables

Create a `.env` file in the project root:

```bash
copy .env.example .env
```

Add your configuration:

```env
# OpenAI API Key - Required for CrewAI agents
OPENAI_API_KEY=sk-your-openai-key-here

# Target API Configuration
API_URL=https://api.example.com/users/submit
API_TOKEN=your-api-bearer-token-here
```

### Step 3: Customize API Schema

Edit `src/extract_pdf/config/api_schema.json` to match your API requirements:
- Define required fields for user information
- Specify user history data structure
- Set validation rules and data types

## Running the Project

### Basic Usage

```bash
crewai run path/to/your/document.pdf
```

Or run without arguments to be prompted:

```bash
crewai run
```

### What Happens

1. **PDF Extractor Agent** reads your PDF and extracts all text content
2. **Data Mapping Specialist** transforms the data into your API's JSON format
3. **API Integration Agent** validates the JSON against your schema
4. **API Integration Agent** POSTs the validated data to your API endpoint

### Output Files

- `formatted_data.json` - The validated JSON data ready for API
- `api_response.json` - The response received from your API

## Project Structure

```
extract_pdf/
├── .env                          # Your API keys and configuration
├── .env.example                  # Template for .env
├── pyproject.toml               # Project dependencies
├── src/
│   └── extract_pdf/
│       ├── main.py              # Entry point
│       ├── crew.py              # Crew and agent definitions
│       ├── config/
│       │   ├── agents.yaml      # Agent configurations
│       │   ├── tasks.yaml       # Task definitions
│       │   └── api_schema.json  # Your API schema
│       └── tools/
│           └── custom_tool.py   # PDF, validation, and API tools
└── SETUP_GUIDE.md               # Detailed setup instructions
```

## The Agents

### 1. PDF Extractor Agent
- **Role**: PDF Data Extraction Specialist
- **Tools**: PDFExtractorTool
- **Goal**: Extract all user information and history data from PDF files

### 2. Data Mapping Specialist
- **Role**: API Data Mapping and Formatting Specialist
- **Goal**: Transform extracted data into exact API schema format

### 3. API Integration Agent
- **Role**: API Validation and Integration Specialist
- **Tools**: JSONValidatorTool, APIPostTool
- **Goal**: Validate JSON format and successfully POST to API

## Customization

### Modify Agents
Edit `src/extract_pdf/config/agents.yaml` to customize agent behavior, roles, and goals.

### Modify Tasks
Edit `src/extract_pdf/config/tasks.yaml` to adjust the extraction and mapping logic.

### Update API Schema
Edit `src/extract_pdf/config/api_schema.json` to match your API requirements.

### Add Custom Tools
Create additional tools in `src/extract_pdf/tools/custom_tool.py` for specialized processing.

### Add Custom Tools
Create additional tools in `src/extract_pdf/tools/custom_tool.py` for specialized processing.

## Use Cases

- **Process user registration forms** from PDF to backend system
- **Extract invoice data** and submit to accounting API
- **Import customer records** from PDF documents to CRM
- **Automate document processing** with validation and API integration

## Troubleshooting

See `SETUP_GUIDE.md` for detailed troubleshooting steps.

### Common Issues

- **PDF not extracting**: Ensure PDF contains text (not scanned images)
- **JSON validation fails**: Check schema matches your API requirements
- **API POST fails**: Verify API_URL and API_TOKEN in .env file

## Support

For support, questions, or feedback:
- Visit [CrewAI documentation](https://docs.crewai.com)
- Check our [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions
- Review [GitHub repository](https://github.com/joaomdmoura/crewai)
- [Join CrewAI Discord](https://discord.com/invite/X4JWnZnxPb)

---

**Built with CrewAI - Orchestrating AI Agents for Complex Tasks**

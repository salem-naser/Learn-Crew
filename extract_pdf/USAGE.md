# PDF to JSON Extraction - Usage Guide

## Overview
This project uses CrewAI to extract data from PDF files and convert it to structured JSON format.

## Setup

### 1. Install Dependencies
```bash
pip install PyPDF2
crewai install
```

### 2. Set up Environment Variables
Create a `.env` file in the project root with your OpenAI API key:
```
OPENAI_API_KEY=your_openai_api_key_here
```

## How to Use

### Method 1: Run with PDF path as argument
```bash
crewai run path/to/your/document.pdf
```

### Method 2: Run and enter path when prompted
```bash
crewai run
```
Then enter the PDF file path when prompted.

### Method 3: Run directly with Python
```bash
python src/extract_pdf/main.py path/to/your/document.pdf
```

## Output

The extracted data will be saved to `extracted_data.json` in the project root directory.

## How It Works

1. **PDF Extractor Agent**: Reads the PDF file and extracts all text content from each page
2. **Data Analyst Agent**: Takes the extracted text and structures it into a clean JSON format

## Agents

- **pdf_extractor**: Specializes in extracting data from PDF files
- **data_analyst**: Transforms extracted data into structured JSON format

## Tasks

- **extract_pdf_task**: Extracts all text and data from the PDF
- **structure_to_json_task**: Converts extracted data to JSON format

## Example

```bash
# Extract data from invoice.pdf
crewai run invoice.pdf

# Output will be saved to extracted_data.json
```

## Troubleshooting

- Make sure the PDF file path is correct and the file exists
- Ensure you have set up your OPENAI_API_KEY in the .env file
- Check that all dependencies are installed: `pip list | grep -i "crewai\|pypdf2"`

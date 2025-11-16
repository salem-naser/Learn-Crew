# PDF to JSON Extraction - Complete Setup Guide

## 📋 Prerequisites

- Python 3.10 - 3.13 installed
- pip package manager
- OpenAI API key
- PDF files you want to extract data from

## 🚀 Step-by-Step Setup

### Step 1: Navigate to Project Directory


### Step 2: Install UV Package Manager (if not installed)

```powershell
pip install uv
```

### Step 3: Install Project Dependencies

```powershell
crewai install
```

This will install:
- CrewAI framework with tools
- PyPDF2 for PDF processing
- All other required dependencies

### Step 4: Configure Environment Variables

1. Copy the example environment file:
```powershell
copy .env.example .env
```

2. Open `.env` file in your editor

3. Add your OpenAI API key:
```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

**How to get OpenAI API Key:**
- Go to https://platform.openai.com/api-keys
- Sign in or create an account
- Click "Create new secret key"
- Copy the key and paste it in your `.env` file

### Step 5: Prepare Your PDF Files

Place your PDF files in an accessible location, for example:
- `c:\Users\DTS\Desktop\pdfs\invoice.pdf`
- `c:\Users\DTS\Desktop\pdfs\report.pdf`

## ▶️ Running the Extraction

### Method 1: Run with PDF Path

```powershell
crewai run "c:\path\to\your\document.pdf"
```

### Method 2: Interactive Mode

```powershell
crewai run
```

Then enter the PDF path when prompted:
```
Enter the path to your PDF file: c:\path\to\your\document.pdf
```

### Method 3: Direct Python Execution

```powershell
python src\extract_pdf\main.py "c:\path\to\your\document.pdf"
```

## 📤 Understanding the Output

### Output File: `extracted_data.json`

The system creates a JSON file with structured data from your PDF:

```json
{
  "title": "Document Title",
  "sections": [
    {
      "heading": "Section 1",
      "content": "Text content from section..."
    }
  ],
  "metadata": {
    "pages": 5,
    "extraction_date": "2025-11-16"
  }
}
```

The exact structure depends on your PDF content and how the AI agent analyzes it.

## 🔧 How the System Works

### Architecture

```
PDF File → PDF Extractor Agent → Raw Text Data → Data Analyst Agent → JSON Output
```

### Agents

1. **PDF Extractor Agent**
   - Role: PDF Data Extraction Specialist
   - Reads PDF files page by page
   - Extracts text, numbers, and structured data
   - Uses PyPDF2 library

2. **Data Analyst Agent**
   - Role: Data Structuring and JSON Specialist
   - Analyzes extracted text
   - Identifies patterns and structure
   - Creates well-formatted JSON output

### Tasks Flow

1. **Extract PDF Task**
   - Input: PDF file path
   - Process: Extract all text from PDF
   - Output: Raw text organized by pages

2. **Structure to JSON Task**
   - Input: Extracted text data
   - Process: Analyze and structure data
   - Output: Clean JSON file (`extracted_data.json`)

## 📁 Project Structure

```
extract_pdf/
├── .env                          # Your API keys (create this)
├── .env.example                  # Template for .env
├── pyproject.toml               # Project dependencies
├── extracted_data.json          # Output file (created after run)
├── src/
│   └── extract_pdf/
│       ├── main.py              # Entry point
│       ├── crew.py              # Crew configuration
│       ├── config/
│       │   ├── agents.yaml      # Agent definitions
│       │   └── tasks.yaml       # Task definitions
│       └── tools/
│           └── custom_tool.py   # PDF extraction tool
└── knowledge/
    └── user_preference.txt      # Optional preferences
```

## ✅ Verification Steps

### Check Installation

```powershell
# Verify Python version
python --version

# Verify PyPDF2 is installed
pip list | findstr PyPDF2

# Verify crewai is installed
pip list | findstr crewai
```

### Test with Sample PDF

1. Find or create a simple PDF file
2. Run the extraction:
```powershell
crewai run "path\to\test.pdf"
```
3. Check if `extracted_data.json` is created
4. Open the JSON file to verify output

## 🐛 Troubleshooting

### Issue: "Module not found" error

**Solution:**
```powershell
pip install crewai[tools]==1.4.1
pip install PyPDF2
```

### Issue: "OPENAI_API_KEY not found"

**Solution:**
- Verify `.env` file exists in project root
- Check that the key is properly formatted: `OPENAI_API_KEY=sk-...`
- Restart your terminal after creating `.env`

### Issue: "PDF file not found"

**Solution:**
- Use absolute paths: `c:\full\path\to\file.pdf`
- Use quotes around paths with spaces
- Check file extension is `.pdf`

### Issue: "Permission denied" when reading PDF

**Solution:**
- Close the PDF if it's open in another program
- Check file permissions
- Try copying PDF to a different location

### Issue: CrewAI command not found

**Solution:**
```powershell
# Install UV first
pip install uv

# Then run
crewai install
```

## 🎯 Example Use Cases

### Extract Invoice Data
```powershell
crewai run "c:\invoices\invoice_2025.pdf"
```
Output: Structured JSON with invoice number, date, items, amounts

### Extract Resume Information
```powershell
crewai run "c:\resumes\john_doe.pdf"
```
Output: JSON with name, skills, experience, education

### Extract Report Data
```powershell
crewai run "c:\reports\monthly_report.pdf"
```
Output: JSON with report sections, data points, summaries

## 🔄 Next Steps

1. **Customize Agents** - Edit `src/extract_pdf/config/agents.yaml` to modify agent behavior
2. **Modify Tasks** - Edit `src/extract_pdf/config/tasks.yaml` to change extraction logic
3. **Add More Tools** - Create additional tools in `src/extract_pdf/tools/`
4. **Process Multiple PDFs** - Create a loop script to process multiple files

## 📚 Additional Resources

- [CrewAI Documentation](https://docs.crewai.com)
- [PyPDF2 Documentation](https://pypdf2.readthedocs.io/)
- [OpenAI API Documentation](https://platform.openai.com/docs)

## 💡 Tips for Best Results

1. **PDF Quality**: Works best with text-based PDFs (not scanned images)
2. **API Costs**: Monitor your OpenAI usage as each extraction uses API calls
3. **Complex PDFs**: May require adjusting agent prompts in YAML files
4. **Large PDFs**: Processing time depends on PDF size and complexity

## 🆘 Support

If you encounter issues:
1. Check this guide's troubleshooting section
2. Verify all prerequisites are met
3. Review the error messages carefully
4. Check that `.env` file is configured correctly

---

**Happy Extracting! 🎉**

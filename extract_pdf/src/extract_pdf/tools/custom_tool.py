from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import PyPDF2
import json
from pathlib import Path


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

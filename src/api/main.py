"""
MINIMAL Backend - Just PDF Upload → JSON
For CDC-CGI Project
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import sys
import json
import tempfile
import os

# Add src to path so we can import pdf_parser
sys.path.insert(0, str(Path(__file__).parent.parent))

from extraction.pdf_parser import parse_pdf_to_json

app = FastAPI(
    title="CDC-CGI Payslip Upload API",
    description="Upload PDF payslips and get JSON output",
    version="1.0.0"
)

# CORS - allow frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "CDC-CGI Payslip Upload API",
        "status": "operational",
        "endpoint": "/upload"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF payslip and get back the parsed JSON data
    
    Returns:
    - success: True/False
    - filename: Original filename
    - data: Parsed bulletin data (JSON)
    - message: Success/error message
    """
    
    # Check if it's a PDF
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=400, 
            detail="Only PDF files accepted. Please upload a .pdf file."
        )
    
    # Save PDF temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # Parse PDF using teammates' parser
        bulletins = parse_pdf_to_json(Path(tmp_path))
        
        if not bulletins or len(bulletins) == 0:
            raise HTTPException(
                status_code=400,
                detail="Could not parse PDF. Make sure it's a valid payslip."
            )
        
        # Success! Return the parsed data
        return {
            "success": True,
            "filename": file.filename,
            "bulletins_count": len(bulletins),
            "data": bulletins,
            "message": f"Successfully parsed {len(bulletins)} bulletin(s)"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error parsing PDF: {str(e)}"
        )
    
    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting CDC-CGI Backend...")
    print("📍 API will be available at: http://localhost:8000")
    print("📖 Docs available at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)

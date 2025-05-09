import os
import time
import shutil
import logging
import tempfile
from app.document import document
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from app.embedding import embedding

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="Docling Ingestion API",
    description="API for PDF-to-embedding pipeline",
    version="1.0.0"
)


@app.get(
    path="/healthcheck",
    status_code=200,
    response_model=dict,
    summary="Health check endpoint"
)
def healthcheck():
    return {"status": "ok"}


@app.post(
    path="/ingest/pdf",
    status_code=200,
    response_model=dict,
    summary="Ingest PDF endpoint",
    description="Accept a PDF file, process it (convert, chunk, embed), and send to Qdrant."
)
async def ingest_pdf(
        file: UploadFile = File(...),
):
    """
    Accept a PDF file, process it (convert, chunk, embed), and send to Qdrant.
    """

    temp_pdf_path: str = ""

    # Check if the file is a PDF
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Save the uploaded PDF to a temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
        shutil.copyfileobj(file.file, temp_pdf)
        temp_pdf_path = temp_pdf.name

    try:

        collection_name = os.path.splitext(os.path.basename(file.filename))[0]

        logger.info(collection_name)

        logger.info(f"Temp PDF path: {temp_pdf_path}")

        start_ingestion = time.time()

        # Convert PDF to Markdown with OCR (returns Markdown text or list of md file paths)
        embedding_result = document.pdf_to_docling_with_ocr(temp_pdf_path, collection_name)

        end_ingestion = time.time()
        logger.info(f"Time to process ingestion: {end_ingestion - start_ingestion} seconds")

        return {
            "message": "Pipeline completed successfully",
            "filename": file.filename,
            "markdown_file": file.filename.lower().replace('.pdf', '.md'),
            "embedding_result": embedding_result
        }

    except FileNotFoundError:

        raise HTTPException(status_code=404, detail=f"File not found during processing: {temp_pdf_path}")

    except Exception as e:

        raise HTTPException(status_code=500, detail=f"Error in pipeline: {str(e)}")

    finally:

        if os.path.exists(temp_pdf_path):
            os.unlink(temp_pdf_path)

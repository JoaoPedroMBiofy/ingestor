import os
import requests
from pathlib import Path
from pypdf import PdfReader, PageObject
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, TesseractCliOcrOptions

def create_tesseract_converter() -> DocumentConverter:
    """Create a converter with Tesseract OCR options."""

    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = True
    pipeline_options.do_table_structure = True
    pipeline_options.generate_page_images = True
    pipeline_options.table_structure_options.do_cell_matching = True

    ocr_options = TesseractCliOcrOptions(force_full_page_ocr=True)
    ocr_options.lang = ["por"]
    pipeline_options.ocr_options = ocr_options

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    return converter


def get_pdf_pages(pdf_path_string: str) -> list[PageObject]:
    """Return all the PDF pages."""

    try:

        reader = PdfReader(pdf_path_string)

        pages = [page for page in reader.pages]

        return pages

    except Exception as e:

        print(f"ERROR: {e}")
        raise []


def create_page_path(page_pdf_folder: str, pdf_name: str, page_name: str) -> str:
    """Create the path to the page PDF file."""

    pdf_page_path = os.path.join(f"{page_pdf_folder}/{pdf_name}", page_name + ".pdf")
    os.makedirs(os.path.dirname(pdf_page_path), exist_ok=True)

    return pdf_page_path


def convert_text_to_markdown(page_path_string: str, converter: DocumentConverter) -> str:
    """Convert text generated from OCR to Markdown format with docling."""

    try:

        page_path = Path(page_path_string)

        document_converted = converter.convert(page_path)

        document_converted_in_markdown = document_converted.document.export_to_markdown()

        return document_converted_in_markdown

    except Exception as e:

        print("ERROR ", str(e))
        raise e


def concat_markdown_pages_into_file(markdown_pages: list[str], full_file_markdown_folder: str,  markdown_file_path: str) -> str:
    """Concatenate all pages generated from docling into a single file."""

    full_path = os.path.join(full_file_markdown_folder, markdown_file_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    with open(full_path, "w") as f:

        for page in markdown_pages:

            f.write(page)
            f.write("\n\n")

    return full_path


def put_markdown_file_into_oci_bucket(entire_pdf_path: str, pdf_name: str, suffix: str):
    """Put a file in Markdown into an OCI bucket."""

    with open(entire_pdf_path, "rb") as f:

        request_entire_file = requests.put(
            os.getenv("BUCKET_URL") + f"{pdf_name}/{pdf_name}-{suffix}.md",
            files={'file': f}
        )

    if not request_entire_file.ok:

        print(f"Failed to upload {entire_pdf_path}: {request_entire_file.status_code}")

    else:

        print("request file:", request_entire_file.status_code)
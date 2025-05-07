from pathlib import Path
from pypdf import PdfReader, PageObject, PdfWriter
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


def GetPdfPages(pdf_path: str) -> list[PageObject]:
    """Return all the PDF pages."""
    try:
        reader = PdfReader(pdf_path)

        return [page for page in reader.pages]
    except Exception as e:
        print(f"ERROR: {e}")
        raise []


def ConvertTextToMarkdown(page_path: str, converter: DocumentConverter) -> str:
    """Convert text generated from OCR to Markdown format with docling."""

    try:
        page_path = Path(page_path)

        document_converted = converter.convert(page_path)

        document_converted_markdown = document_converted.document.export_to_markdown()

        return document_converted_markdown

    except Exception as e:

        print("ERROR ", str(e))
        raise e
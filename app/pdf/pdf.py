import os
import glob
import logging
from pathlib import Path
from pypdf import PdfReader
from pypdf import PdfWriter
from pypdf import PageObject
from docling.datamodel.base_models import InputFormat
from docling.document_converter import PdfFormatOption
from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.pipeline_options import TesseractCliOcrOptions

# Create a logger for this module
logger = logging.getLogger(__name__)


def create_tesseract_converter() -> DocumentConverter:
    """
    Create a converter with Tesseract OCR options.
    """

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


def get_pdf_pages(
        pdf_path_string: str
) -> list[PageObject]:
    """
    Return all the PDF pages.
    """

    try:

        reader = PdfReader(pdf_path_string)

        pages = [page for page in reader.pages]

        return pages

    except Exception as e:

        logger.error(f"Error getting PDF pages: {e}")
        raise []


def create_page_path(
        pdf_page: PageObject,
        page_pdf_folder: str,
        pdf_name: str,
        page_name: str
) -> str:
    """
    Create the path to the page PDF file.
    """

    pdf_dir = os.path.join(page_pdf_folder, pdf_name)
    pdf_page_path = os.path.join(pdf_dir, f"{page_name}.pdf")
    os.makedirs(pdf_dir, exist_ok=True)

    # write the page in the pdf_page_path
    writer = PdfWriter()
    writer.add_page(pdf_page)
    writer.write(pdf_page_path)

    return pdf_page_path


def save_temporary_md_file(
        markdown_folder: str,
        pdf_name: str,
        page_name: str,
        md_generated: str
):
    """
    Save the page in Markdown format in a temporary folder.
    """

    # declaring a page path in Markdown and save in markdown_folder
    page_dir = os.path.join(markdown_folder, pdf_name)
    page_path = os.path.join(page_dir, f"{page_name}.md")
    os.makedirs(page_dir, exist_ok=True)

    with open(page_path, "w") as f:
        f.write(md_generated)


def convert_text_to_markdown(
        page_path_string: str,
        converter: DocumentConverter
) -> str:
    """
    Convert text generated from OCR to Markdown format with docling.
    """

    try:

        page_path = Path(page_path_string)

        document_converted = converter.convert(page_path)

        document_converted_in_markdown = document_converted.document.export_to_markdown()

        return document_converted_in_markdown

    except Exception as e:

        logger.error(f"Error converting text to markdown: {e}")
        raise e


def concat_markdown_pages_into_file(
        markdown_folder: str,
        pdf_name: str,
        output_dir: str,
        markdown_file_name: str
) -> str:
    """
    Concatenate all Markdown page files from the markdown_folder (by pdf_name subfolder) into one file.
    - markdown_folder: Temporary folder where page markdowns are stored.
    - pdf_name: The name (without extension) of the PDF.
    - output_dir: The (persistent) directory where the final Markdown will be saved.
    - markdown_file_name: The name of the final Markdown file (e.g., "filename.md").
    Returns: The path to the generated Markdown file.
    """

    # Path to the directory containing markdown pages: <markdown_folder>/<pdf_name>
    pages_dir = os.path.join(markdown_folder, pdf_name)
    if not os.path.exists(pages_dir):
        raise FileNotFoundError(f"Markdown pages folder not found: {pages_dir}")

    # Collect all Markdown files in the subfolder, sort by page number
    md_files = sorted(
        glob.glob(os.path.join(pages_dir, f"{pdf_name}-*.md")),
        key=lambda x: int(os.path.splitext(x)[0].split('-')[-1])  # sorts by page number
    )

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, markdown_file_name)

    with open(output_path, "w") as f:
        for md_file in md_files:
            with open(md_file, "r") as fin:
                f.write(fin.read())
                f.write("\n\n")

    return output_path

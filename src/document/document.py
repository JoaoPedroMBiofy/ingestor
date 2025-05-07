import os
import time
from src.utils.utils import *

def pdf_to_docling_with_ocr(pdf_path: str) -> list:
    """Convert a PDF to images and perform Docling with OCR on each page."""

    page_pdf_folder = os.getenv("PAGE_PDF_FOLDER")
    markdown_folder = os.getenv("MARKDOWN_PAGE_FOLDER")
    full_file_markdown_folder = os.getenv("FULL_FILE_MARKDOWN_FOLDER")

    # get the PDF name
    pdf_name, _ = os.path.splitext(os.path.basename(pdf_path))

    print(f"Converting {pdf_name} to images")

    # pages from the PDF and store in the image folder
    start_pdf_pages_extraction = time.time()

    pdf_pages = get_pdf_pages(pdf_path)

    end_pdf_pages_extraction = time.time()
    print("Time to process: ", end_pdf_pages_extraction - start_pdf_pages_extraction, " seconds")

    if len(pdf_pages) == 0:
        print(f"No pages found in {pdf_path}")
        return []

    results = []
    markdown_text_pages = []

    converter = create_tesseract_converter()

    print(f"Converting {pdf_name} pages into text using Docling")

    # enumerate to every page
    for i, pdf_page in enumerate(pdf_pages):

        # declaring page number
        page_number = i + 1

        # declaring the page name
        page_name = f"{pdf_name}-{page_number}"

        # insert the page in a folder
        pdf_page_path = create_page_path(pdf_page, page_pdf_folder, pdf_name, page_name)

        # docling ingestion from PDF page
        start_pdf_pages_ingestion = time.time()

        md_generated = convert_text_to_markdown(pdf_page_path, converter)
        markdown_text_pages.append(md_generated)

        end_pdf_pages_ingestion = time.time()
        print("Time to process: ", end_pdf_pages_ingestion - start_pdf_pages_ingestion, " seconds")


        # declaring a page path in Markdown and save in markdown_folder
        save_temporary_md_file(markdown_folder, pdf_name, page_name, md_generated)

        # put every page from the PDF Markdown file into oci bucket
        # put_file_page_into_oci_bucket(page_path, pdf_name, i + 1)

        results.append((pdf_name, page_name, "OK"))

        # concat every page in a single file '.md'
        start_concat_markdown_pages = time.time()

        full_markdown_file = concat_markdown_pages_into_file(markdown_text_pages, full_file_markdown_folder+"-docling", pdf_name + ".md")

        end_concat_markdown_pages = time.time()
        print("Time to process: ", end_concat_markdown_pages - start_concat_markdown_pages, " seconds")

        print(f"Saving Markdown file: {pdf_name}.md")

        # put the PDF in Markdown into oci bucket
        start_put_markdown_file_into_oci_bucket = time.time()

        put_markdown_file_into_oci_bucket(full_markdown_file, pdf_name, "docling")

        end_put_markdown_file_into_oci_bucket = time.time()
        print("Time to process: ", end_put_markdown_file_into_oci_bucket - start_put_markdown_file_into_oci_bucket, " seconds")

    return results
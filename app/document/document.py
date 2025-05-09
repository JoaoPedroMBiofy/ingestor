import os
import time
import logging
import tempfile
from app.pdf import pdf
# from app.utils import utils

# Create a logger for this module
logger = logging.getLogger(__name__)


def pdf_to_docling_with_ocr(
        pdf_path: str,
        output_dir: str = "./output"
) -> str:
    """
    Convert a PDF to images and perform Docling with OCR on each page.
    Temporary folders are used for page images and page markdowns,
    while the final concatenated Markdown file is saved to `output_dir`.
    """

    os.makedirs(output_dir, exist_ok=True)

    with tempfile.TemporaryDirectory() as page_pdf_folder, \
            tempfile.TemporaryDirectory() as markdown_folder:

        # get the PDF name
        pdf_name, _ = os.path.splitext(os.path.basename(pdf_path))

        logger.info(f"Converting {pdf_name} to images")

        # pages from the PDF and store in the image folder
        start_pdf_pages_extraction = time.time()
        pdf_pages = pdf.get_pdf_pages(pdf_path)
        end_pdf_pages_extraction = time.time()
        logger.info(f"[EXTRACT PDF PAGES] Time to process: {end_pdf_pages_extraction - start_pdf_pages_extraction} seconds")

        if len(pdf_pages) == 0:
            logger.warning(f"No pages found in {pdf_path}")
            return ""

        converter = pdf.create_tesseract_converter()

        logger.info(f"Converting {pdf_name} pages into text using Docling")

        # enumerate to every page
        for i, pdf_page in enumerate(pdf_pages):

            page_number = i + 1
            page_name = f"{pdf_name}-{page_number}"
            pdf_page_path = pdf.create_page_path(
                pdf_page=pdf_page,
                page_pdf_folder=page_pdf_folder,
                pdf_name=pdf_name,
                page_name=page_name
            )

            logger.info(f"Processing page {page_number} of {pdf_name}")

            # docling ingestion from PDF page
            start_pdf_pages_ingestion = time.time()
            md_generated = pdf.convert_text_to_markdown(
                page_path_string=pdf_page_path,
                converter=converter,
            )
            end_pdf_pages_ingestion = time.time()
            logger.info(f"[DOCLING PAGE INGESTION] Time to process: {end_pdf_pages_ingestion - start_pdf_pages_ingestion} seconds")

            # save individual page markdowns to a temp folder
            pdf.save_temporary_md_file(
                markdown_folder=markdown_folder,
                pdf_name=pdf_name,
                page_name=page_name,
                md_generated=md_generated
            )

        # concatenate all Markdown pages into a single file (persistently)
        start_concat_markdown_pages = time.time()
        full_markdown_file = pdf.concat_markdown_pages_into_file(
            markdown_folder=markdown_folder,
            pdf_name=pdf_name,
            output_dir=output_dir,
            markdown_file_name=pdf_name + ".md"
        )
        end_concat_markdown_pages = time.time()
        logger.info(f"[CONCAT MD FILES] Time to process: {end_concat_markdown_pages - start_concat_markdown_pages} seconds")

        logger.info(f"Full Markdown file saved to {full_markdown_file}")

        # # upload to OCI bucket
        # start_put_markdown_file_into_oci_bucket = time.time()
        # utils.put_markdown_file_into_oci_bucket(
        #     full_markdown_file,
        #     pdf_name,
        #     "docling"
        # )
        # end_put_markdown_file_into_oci_bucket = time.time()
        # logger.info(f"[OCI UPLOAD MD FILE] Time to process: {end_put_markdown_file_into_oci_bucket - start_put_markdown_file_into_oci_bucket} seconds")

    return full_markdown_file

import os
import time
import logging
import tempfile
from app.pdf import pdf
from app.embedding import embedding

# Create a logger for this module
logger = logging.getLogger(__name__)


def pdf_to_docling_with_ocr(
        pdf_path: str,
        collection_name: str,
        output_dir: str = "./output"
) -> list[dict]:
    """
    Convert a PDF to images and perform Docling with OCR on each page.
    Temporary folders are used for page images and page markdowns,
    while the final concatenated Markdown file is saved to `output_dir`.
    """

    embedding_result_list = []

    os.makedirs(output_dir, exist_ok=True)

    with tempfile.TemporaryDirectory() as page_pdf_folder, tempfile.TemporaryDirectory() as markdown_folder:

        # get the PDF name
        pdf_name, _ = os.path.splitext(os.path.basename(pdf_path))

        logger.info(f"Converting {pdf_name} to images")

        # pages from the PDF and store in the image folder
        pdf_pages = pdf.get_pdf_pages(pdf_path)

        if len(pdf_pages) == 0:
            logger.warning(f"No pages found in {pdf_path}")
            raise "No pages found in PDF. Please check the PDF file."

        converter = pdf.create_tesseract_converter()

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
            logger.info(f"Time to process conversion: {end_pdf_pages_ingestion - start_pdf_pages_ingestion} seconds")

            # save individual page markdowns to a temp folder
            page_path = pdf.save_temporary_md_file(
                markdown_folder=markdown_folder,
                pdf_name=pdf_name,
                page_name=page_name,
                md_generated=md_generated
            )

            logger.info("Start File Pipeline")
            # Create embeddings and send to Qdrant
            start_pipeline = time.time()
            embedding_result = embedding.create_embeddings_from_markdown(
                markdown_file=page_path,
                collection_name=collection_name,
            )
            end_pipeline = time.time()
            logger.info(f"Time to process pipeline: {end_pipeline - start_pipeline} seconds")

            embedding_result_list.append(embedding_result)

        # # concatenate all Markdown pages into a single file (persistently)
        # start_concat_markdown_pages = time.time()
        # full_markdown_file = pdf.concat_markdown_pages_into_file(
        #     markdown_folder=markdown_folder,
        #     pdf_name=pdf_name,
        #     output_dir=output_dir,
        #     markdown_file_name=pdf_name + ".md"
        # )
        # end_concat_markdown_pages = time.time()
        # logger.info(f"[CONCAT MD FILES] Time to process: {end_concat_markdown_pages - start_concat_markdown_pages} seconds")
        #
        # logger.info(f"Full Markdown file saved to {full_markdown_file}")

        # # upload to OCI bucket
        # start_put_markdown_file_into_oci_bucket = time.time()
        # utils.put_markdown_file_into_oci_bucket(
        #     full_markdown_file,
        #     pdf_name,
        #     "docling"
        # )
        # end_put_markdown_file_into_oci_bucket = time.time()
        # logger.info(f"[OCI UPLOAD MD FILE] Time to process: {end_put_markdown_file_into_oci_bucket - start_put_markdown_file_into_oci_bucket} seconds")

    return embedding_result_list

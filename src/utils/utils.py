import os
import requests
from uuid import uuid4
from pathlib import Path
from langchain.schema import Document
from qdrant_client import QdrantClient
from oci.retry import NoneRetryStrategy
from typing import Literal, Optional, List
from langchain.embeddings.base import Embeddings
from pypdf import PdfReader, PageObject, PdfWriter
from docling.datamodel.base_models import InputFormat
from langchain_community.embeddings import OCIGenAIEmbeddings
from langchain_experimental.text_splitter import SemanticChunker
from langchain.text_splitter import RecursiveCharacterTextSplitter
from oci.generative_ai_inference import GenerativeAiInferenceClient
from qdrant_client.models import Distance, VectorParams, PointStruct
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


def get_pdf_pages(
        pdf_path_string: str
) -> list[PageObject]:
    """Return all the PDF pages."""

    try:

        reader = PdfReader(pdf_path_string)

        pages = [page for page in reader.pages]

        return pages

    except Exception as e:

        print(f"ERROR: {e}")
        raise []


def create_page_path(
        pdf_page: PageObject,
        page_pdf_folder: str,
        pdf_name: str,
        page_name: str
) -> str:
    """Create the path to the page PDF file."""

    pdf_page_path = os.path.join(f"{page_pdf_folder}/{pdf_name}/{page_name}.pdf")
    os.makedirs(os.path.dirname(pdf_page_path), exist_ok=True)

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
    """Save the page in Markdown format in a temporary folder."""

    # declaring a page path in Markdown and save in markdown_folder
    page_path = os.path.join(f"{markdown_folder}/{pdf_name}", page_name + ".md")
    os.makedirs(os.path.dirname(page_path), exist_ok=True)

    with open(page_path, "w") as f:
        f.write(md_generated)


def convert_text_to_markdown(
        page_path_string: str,
        converter: DocumentConverter
) -> str:
    """Convert text generated from OCR to Markdown format with docling."""

    try:

        page_path = Path(page_path_string)

        document_converted = converter.convert(page_path)

        document_converted_in_markdown = document_converted.document.export_to_markdown()

        return document_converted_in_markdown

    except Exception as e:

        print("ERROR ", str(e))
        raise e


def concat_markdown_pages_into_file(
        markdown_pages: list[str],
        full_file_markdown_folder: str,
        markdown_file_path: str
) -> str:
    """Concatenate all pages generated from docling into a single file."""

    full_path = os.path.join(full_file_markdown_folder, markdown_file_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    with open(full_path, "w") as f:

        for page in markdown_pages:

            f.write(page)
            f.write("\n\n")

    return full_path


def get_oci_credentials_from_env() -> dict:
    """Gets OCI credentials from the environment."""

    oci_raw_key = os.environ.get('OCI_API_KEY')
    pem_prefix = '-----BEGIN RSA PRIVATE KEY-----\n'
    pem_suffix = '\n-----END RSA PRIVATE KEY-----'
    oci_pem_key_content = '{}{}{}'.format(pem_prefix, oci_raw_key, pem_suffix)

    return dict(
        user=os.environ.get('OCI_USER_ID'),
        key_content=oci_pem_key_content,
        fingerprint=os.environ.get('OCI_FINGERPRINT'),
        tenancy=os.environ.get('OCI_TENANCY_ID'),
        region=os.environ.get('OCI_REGION'),
    )


def oci_genai_client() -> GenerativeAiInferenceClient:
    """Create an OCI GenAI client."""

    return GenerativeAiInferenceClient(
        config=get_oci_credentials_from_env(),
        service_endpoint=os.getenv("OCI_GENAI_ENDPOINT"),
        retry_strategy=NoneRetryStrategy(),
        timeout=(10, 240),
    )


def get_text_splitter(
    strategy: Literal["recursive", "semantic"] = "semantic",
    embeddings_model: Optional[OCIGenAIEmbeddings] = None,
    chunk_size: int = 800,
    chunk_overlap: int = 100,
) -> RecursiveCharacterTextSplitter | SemanticChunker:
    """Return a LangChain-compatible text splitter."""

    if strategy == "semantic":

        if not embeddings_model:

            embeddings_model = OCIGenAIEmbeddings(
                client=oci_genai_client(),
                service_endpoint=os.getenv("OCI_GENAI_ENDPOINT"),
                compartment_id=os.getenv("OCI_TENANCY_ID"),
                model_id=os.getenv("DEFAULT_OCI_EMBEDDING_MODEL"),
            )

        return SemanticChunker(embeddings_model, breakpoint_threshold_type="interquartile")

    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        add_start_index=True
    )


def chunk_and_embed_markdown(
    file_path: str,
    splitter_type: Literal["recursive", "semantic"] = "semantic",
    embeddings_model: Optional[OCIGenAIEmbeddings] = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 100,
) -> List[Document]:
    """Load, chunk, and embed a Markdown file using LangChain."""

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    splitter = get_text_splitter(
        strategy=splitter_type,
        embeddings_model=embeddings_model,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    chunks = splitter.split_text(raw_text)

    documents = [
        Document(
            page_content=chunk,
            metadata={"source_file": os.path.basename(file_path)}
        )
        for chunk in chunks if chunk.strip()
    ]

    return documents


def send_embed_to_qdrant(
    collection_name: str,
    documents: List[Document],
    embeddings_model: Embeddings,
    qdrant_host: str = "localhost",
    qdrant_port: int = 6333,
) -> None:
    """Embeds the documents and stores them in Qdrant."""

    # Initialize Qdrant client
    client = QdrantClient(host=qdrant_host, port=qdrant_port)

    # Create a collection if not exists
    if collection_name not in [c.name for c in client.get_collections().collections]:

        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=len(embeddings_model.embed_query("test")),  # infer vector size
                distance=Distance.COSINE,
            )
        )

    # Generate embeddings
    texts = [doc.page_content for doc in documents]
    embeddings = embeddings_model.embed_documents(texts)

    # Prepare and send points
    points = [
        PointStruct(
            id=str(uuid4()),
            vector=vector,
            payload=doc.metadata
        )
        for doc, vector in zip(documents, embeddings)
    ]

    client.upsert(collection_name=collection_name, points=points)
    print(f"✅ Uploaded {len(points)} embeddings to Qdrant collection '{collection_name}'")


def put_markdown_file_into_oci_bucket(
        entire_pdf_path: str,
        pdf_name: str,
        suffix: str
):
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
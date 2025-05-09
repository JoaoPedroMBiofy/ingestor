import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# load_dotenv()

class Config(BaseSettings):

    OCI_USER_ID: str = os.getenv("OCI_USER_ID")
    OCI_FINGERPRINT: str = os.getenv("OCI_FINGERPRINT")
    OCI_TENANCY_ID: str = os.getenv("OCI_TENANCY_ID")
    OCI_REGION: str = os.getenv("OCI_REGION")
    OCI_API_KEY: str = os.getenv("OCI_API_KEY")

    OCI_GEN_AI_ENDPOINT: str = os.getenv("OCI_GEN_AI_ENDPOINT")
    DEFAULT_OCI_EMBEDDING_MODEL: str = os.getenv("DEFAULT_OCI_EMBEDDING_MODEL")

    OCI_BUCKET_URL: str = os.getenv("OCI_BUCKET_URL")

    QDRANT_HOST: str = os.getenv("QDRANT_HOST")
    QDRANT_PORT: str = os.getenv("QDRANT_PORT")

    MAX_WORKERS: int = os.getenv("MAX_WORKERS")

    PAGE_PDF_FOLDER: str = "page_pdf"
    MARKDOWN_PAGE_FOLDER: str = "markdown_page"
    FULL_FILE_MARKDOWN_FOLDER: str = "full_file_markdown"
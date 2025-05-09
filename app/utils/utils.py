import requests
import logging
from app.config import config
from oci.config import validate_config
from oci.retry import NoneRetryStrategy
from langchain_community.embeddings import OCIGenAIEmbeddings
from oci.generative_ai_inference import GenerativeAiInferenceClient

# Create a logger for this module
logger = logging.getLogger(__name__)

# Config obj
config_env = config.Config()


def put_markdown_file_into_oci_bucket(
        entire_pdf_path: str,
        pdf_name: str,
        suffix: str
):
    """
    Put a file in Markdown into an OCI bucket.
    """

    with open(entire_pdf_path, "rb") as f:

        request_entire_file = requests.put(
            config_env.OCI_BUCKET_URL + f"{pdf_name}/{pdf_name}-{suffix}.md",
            files={'file': f}
        )

    if not request_entire_file.ok:

        logger.error(f"Failed to upload {entire_pdf_path}: {request_entire_file.status_code}")

    else:

        logger.info(f"File upload successful: {request_entire_file.status_code}")


def get_oci_credentials_from_env() -> dict:
    """
    Gets OCI credentials from the environment.
    """

    oci_raw_key = config_env.OCI_API_KEY
    pem_prefix = '-----BEGIN RSA PRIVATE KEY-----\n'
    pem_suffix = '\n-----END RSA PRIVATE KEY-----'
    oci_pem_key_content = '{}{}{}'.format(pem_prefix, oci_raw_key, pem_suffix)

    return dict(
        user=config_env.OCI_USER_ID,
        key_content=oci_pem_key_content,
        fingerprint=config_env.OCI_FINGERPRINT,
        tenancy=config_env.OCI_TENANCY_ID,
        region=config_env.OCI_REGION,
    )


def default_embed_model() -> OCIGenAIEmbeddings:
    """
    Create an OCI GenAI embeddings model.
    """

    embeddings_model = OCIGenAIEmbeddings(
        client=oci_genai_client(),
        service_endpoint=config_env.OCI_GEN_AI_ENDPOINT,
        compartment_id=config_env.OCI_TENANCY_ID,
        model_id=config_env.DEFAULT_OCI_EMBEDDING_MODEL,
    )
    return embeddings_model

def oci_genai_client() -> GenerativeAiInferenceClient:
    """
    Create an OCI GenAI client.
    """

    return GenerativeAiInferenceClient(
        config=get_oci_credentials_from_env(),
        service_endpoint=config_env.OCI_GEN_AI_ENDPOINT,
        retry_strategy=NoneRetryStrategy(),
        timeout=(10, 240),
    )

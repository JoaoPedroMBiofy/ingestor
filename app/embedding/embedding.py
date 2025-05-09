import os
import logging
from app.utils import utils
from app.config import config
from langchain.schema import Document
from qdrant_client import QdrantClient
from qdrant_client.models import Distance
from langchain_qdrant import QdrantVectorStore
from typing import Literal, List
from qdrant_client.models import VectorParams
from langchain_community.embeddings import OCIGenAIEmbeddings
from langchain_experimental.text_splitter import SemanticChunker
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Create a logger for this module
logger = logging.getLogger(__name__)

# config obj
config_env = config.Config()


def get_text_splitter(
    embeddings_model: OCIGenAIEmbeddings,
    name: Literal[
        'recursive_character',
        'semantic_chunker'
    ]
):
    text_splitters_factory = {
        'recursive_character': RecursiveCharacterTextSplitter(
            chunk_size=1700, chunk_overlap=80, add_start_index=True
        ),
        'semantic_chunker': SemanticChunker(
            embeddings_model, breakpoint_threshold_type='interquartile'
        ),
    }
    return text_splitters_factory[name]


def chunk_and_embed_markdown(
    file_path: str,
    embeddings_model: OCIGenAIEmbeddings,
    strategy: Literal["recursive_character", "semantic_chunker"]
) -> List[Document]:
    """
    Load, chunk, and embed a Markdown file using LangChain.
    """

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    logger.info(f"Processing Markdown file: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    text_splitter = get_text_splitter(embeddings_model, strategy)

    logger.info(f"Text splitter: {type(text_splitter)}")

    if type(text_splitter) is SemanticChunker:

        try:
            docs = text_splitter.create_documents([raw_text])
        except Exception as e:
            logger.error(f"Error [SEMANTIC] splitting text: {e}")
            raise e

        logger.info(f"Documents: {docs}")

        return docs

    else:

        try:
            chunks = text_splitter.split_text(raw_text)
        except Exception as e:
            logger.error(f"Error [RECURSIVE] splitting text: {e}")
            raise e

        logger.info(f"Chunks: {chunks}")

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
    embeddings_model: OCIGenAIEmbeddings,
    qdrant_host: str,
    qdrant_port: int
) -> None:
    """
    Embeds the documents and stores them in Qdrant.
    """

    try:
        # Initialize Qdrant client
        client = QdrantClient(host=qdrant_host, port=qdrant_port)
    except Exception as e:
        logger.error(f"Error initializing Qdrant client: {e}")
        raise e

    logger.info(f"Connected to Qdrant Client: {client}")

    if not documents:
        logger.info("No documents to process")
        raise "No documents to process"

    try:
        if not client.collection_exists(collection_name):
            logger.info(f"Create new collection: {collection_name}")

            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=1024,
                    distance=Distance.COSINE,
                )
            )
    except Exception as e:
        logger.error(f"Error creating collection: {e}")
        raise e

    logger.info(f"Time to Embed")

    try:
        vector_store = QdrantVectorStore(
            client=client,
            collection_name=collection_name,
            distance=Distance.COSINE,
            embedding=embeddings_model,
        )
        vector_store.add_documents(documents=documents)
    except Exception as e:
        logger.error(f"Error adding documents to Qdrant: {e}")
        raise e

    # this is langchain didn't exist
    # # Generate embeddings
    # texts = [doc.page_content for doc in documents]
    #
    # try:
    #     embeddings = embeddings_model.embed_documents(texts)
    # except Exception as e:
    #     logger.error(f"Error generating embeddings: {e}")
    #     raise e
    #
    # logger.info(f"Generated Embeddings {len(embeddings)}")
    #
    # try:
    #
    #     # client.upsert(
    #     #     collection_name=collection_name,
    #     #     points=[
    #     #         PointStruct(
    #     #             id=str(uuid4()),
    #     #             vector=vector,
    #     #             payload={"doc": doc.metadata}
    #     #         )
    #     #         for doc, vector in zip(documents, embeddings)
    #     #     ]
    #     # )
    # except Exception as e:
    #     logger.error(f"Error preparing points: {e}")
    #     raise e

    logger.info(f"Uploaded embeddings to Qdrant collection '{collection_name}'")

    return None


def create_document_from_markdown(
        markdown_file: str,
        collection_name: str = None
) -> list[Document]:
    """
    Create the embeddings for a Markdown file.

    :param markdown_file:
    :param collection_name:
    :return:
    """

    doc_list: list[Document] = []

    with open(markdown_file, "r", encoding="utf-8") as f:
        raw_text = f.read()

    doc = Document(
        page_content=raw_text,
        metadata={"file_name": f"{collection_name}"}
    )
    doc_list.append(doc)

    return doc_list


def create_embeddings_from_markdown(
    markdown_file: str,
    collection_name: str = None,
    strategy: Literal["recursive_character", "semantic_chunker"] = "recursive_character"
) -> dict:
    """
    Create embeddings from a Markdown file and store them in Qdrant.

    Args:
        markdown_file: Path to the Markdown file
        collection_name: Name of the Qdrant collection to store embeddings in
        strategy: Type of text splitter to use

    Returns:
        dict: Information about the embedding process
    """

    logger.info(f"Using collection name: {collection_name}")

    embeddings_model: OCIGenAIEmbeddings

    try:
        # Initialize embeddings model
        embeddings_model = utils.default_embed_model()
    except Exception as e:
        logger.error(f"Error initializing embeddings model: {e}")
        raise e

    logger.info(f"Initialized embeddings model: {embeddings_model}")

    try:
        # transform a Markdown file into a document
        documents = create_document_from_markdown(
            markdown_file=markdown_file,
            collection_name=collection_name
        )
    except Exception as e:
        logger.error(f"Error creating document from Markdown file: {e}")
        raise e

    # Chunk the Markdown file
    # documents = chunk_and_embed_markdown(
    #     file_path=markdown_file,
    #     embeddings_model=embeddings_model,
    #     strategy=strategy
    # )

    # Send embeddings to Qdrant
    send_embed_to_qdrant(
        collection_name=collection_name,
        documents=documents,
        embeddings_model=embeddings_model,
        qdrant_host=config_env.QDRANT_HOST,
        qdrant_port=int(config_env.QDRANT_PORT),
    )

    return {
        "collection_name": collection_name,
        "document_count": len(documents),
        "splitter_type": strategy,
    }

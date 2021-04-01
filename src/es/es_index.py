"""
es indexing
"""
import json
import logging

from smart_open import smart_open

from config import config
from embedding import get_embedding
from es.es_setup import es_handler

logger = logging.getLogger(__name__)


def index_page(pageid: int) -> None:
    """
    add page to index
    - get document from s3
    - get embedding from document content
    - prepare es document
    - index es document
    """
    index_name = config.get_es_index()
    s3_bucket = config.get_s3_bucket()
    s3_prefix = config.get_s3_prefix()
    s3_file_uri = f"S3://{s3_bucket}/{s3_prefix}/{pageid}"
    with smart_open(s3_file_uri, "r") as fp:
        page = json.load(fp)

    page_id = page.pop("pageid")
    content = page.pop("content")
    page["uri"] = s3_file_uri
    page["embedding"] = get_embedding(content)

    es_handler.index(index_name, body=page, id=page_id)


if __name__ == "__main__":
    index_page(14559592)
    index_page(3421593)
    index_page(67041708)

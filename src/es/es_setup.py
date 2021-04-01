"""
elastic search interaction module
"""
import logging
from typing import Any

import elasticsearch as es
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ES_URL = config.get_es_url()
ES_AUTH = config.get_es_credentials()
es_handler = es.Elasticsearch([ES_URL], http_auth=ES_AUTH, use_ssl=True, verify_certs=False)


def create_index() -> None:
    """
    create es index in cluster
    """
    index_name = config.get_es_index()
    index_settings = {"number_of_shards": 1, "knn": "true"}
    index_mappings = {
        "properties": {  # id: pageid
            "uri": {"type": "text"},
            "title": {"type": "text"},
            "url": {"type": "text"},
            "embedding": {"type": "knn_vector", "dimension": config.get_embedding_size()},
        }
    }

    index_body = {"settings": index_settings, "mappings": index_mappings}

    es_handler.indices.delete(index_name, ignore_unavailable=True)  # pylint: disable=E1123
    es_handler.indices.create(index_name, body=index_body, params=None, headers=None)


def list_indices() -> Any:
    index_name = config.get_es_index()
    return es_handler.indices.get(index_name)


if __name__ == "__main__":
    logger.info("resetting index disabled by security, uncomment following line to reset index")
    # create_index()

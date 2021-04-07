"""
elastic search interaction module
"""
import logging
from typing import Any

import click

import elasticsearch as es
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ES_URL = config.get_es_url()
ES_AUTH = config.get_es_credentials()
es_handler = es.Elasticsearch([ES_URL], http_auth=ES_AUTH, use_ssl=True, verify_certs=False)


@click.command(help="create index in Elasticsearch cluster")
@click.option("--exists_ok", "-n", type=click.BOOL, default=False, help="delete index if it exists")
def create_index(exists_ok: bool) -> None:
    """
    create es index in cluster
    """
    index_name = config.get_es_index()
    index_settings = {"number_of_shards": 1, "knn": "true"}
    index_mappings = {
        "properties": {
            "uri": {"type": "text"},
            "title": {"type": "text"},
            "url": {"type": "text"},
            "embedding": {"type": "knn_vector", "dimension": config.get_embedding_size()},
        }
    }

    index_body = {"settings": index_settings, "mappings": index_mappings}
    if es_handler.indices.exists_type(index_name):
        if exists_ok:
            es_handler.indices.delete(index_name)  # pylint: disable=E1123
        else:
            raise ValueError(f"Index {index_name} already exists, set 'exists_ok' to True if you want to overwrite it")

    es_handler.indices.create(index_name, body=index_body, params=None, headers=None)


def list_indices() -> Any:
    index_name = config.get_es_index()
    return es_handler.indices.get(index_name)


if __name__ == "__main__":
    create_index()

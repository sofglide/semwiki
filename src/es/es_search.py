"""
elasticsearch search module
"""
import os
from typing import Dict, List

import elasticsearch as es
from config import config
from embedding import get_embedding

es_url = os.getenv("ES_URL")
es_user = os.getenv("ES_USER")
es_password = os.getenv("ES_PASSWORD")
index_name = os.getenv("INDEX_NAME")

es_auth = (es_user, es_password)
es_handler = es.Elasticsearch(es_url, port=443, http_auth=es_auth, use_ssl=True, verify_certs=False)


def get_similar_documents(query: str, count: int) -> List[Dict[str, str]]:
    """
    get similar documents
    """
    index = config.get_es_index()
    embedded_query = get_embedding(query)
    knn_query = {"size": count, "query": {"knn": {"embedding": {"vector": embedded_query, "k": count}}}}

    results = es_handler.search(index=index, body=knn_query)["hits"]["hits"]

    documents = []
    for res in results:
        doc = {"id": res["_id"], "score": res["_score"]}
        source = res["_source"]
        source.pop("embedding")
        doc.update(source)
        documents.append(doc)

    return documents

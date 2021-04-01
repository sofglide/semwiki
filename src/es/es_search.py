"""
elasticsearch search module
"""
from typing import Dict, List

from config import config
from embedding import get_embedding
from es.es_setup import es_handler


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


if __name__ == "__main__":
    get_similar_documents("toto", 2)

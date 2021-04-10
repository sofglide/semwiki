"""
embedding
"""
import json
import logging
from typing import List

import requests

from config import config

logger = logging.getLogger(__name__)


def get_embedding(text: str) -> List[float]:
    """
    send text to embedding service and return embedding
    """
    logger.info(f"embedding text starting with {text[:30]}")
    service_ip = config.get_embedder_ip()
    service_port = config.get("embedder", "port")
    service_endpoint = f"http://{service_ip}:{service_port}/v1/models/USE_3:predict"
    request_data = json.dumps({"instances": [text]})
    resp = requests.post(service_endpoint, data=request_data)
    embedding = resp.json()["predictions"][0]
    return embedding


if __name__ == "__main__":
    print(get_embedding("hello world"))

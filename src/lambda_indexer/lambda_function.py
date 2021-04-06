"""
indexing lambda
"""
import json
import urllib.parse
from typing import Any, List

import boto3
import requests
from smart_open import smart_open

import elasticsearch as es

EMBEDDER_IP = "54.154.40.103"

ES_URL = "https://search-esclust-elasti-dd7hht7lxylw-bpali5yqjubaa4zwb6n2m36s24.eu-west-1.es.amazonaws.com/"
ES_AUTH = ("semwiki", "SemWiki21!")

INDEX_NAME = "semwiki"

es_handler = es.Elasticsearch([ES_URL], http_auth=ES_AUTH, use_ssl=True, verify_certs=False)
s3 = boto3.client("s3")


def get_embedding(text: str) -> List[float]:
    """
    send text to embedding service and return embedding
    """
    service_endpoint = f"http://{EMBEDDER_IP}:8501/v1/models/USE_3:predict"
    request_data = json.dumps({"instances": [text]})
    resp = requests.post(service_endpoint, data=request_data)
    embedding = resp.json()["predictions"][0]
    return embedding


def index_page(s3_bucket: str, s3_key: str) -> None:
    """
    add page to index
    - get document from s3
    - get embedding from document content
    - prepare es document
    - index es document
    """
    s3_file_uri = f"S3://{s3_bucket}/{s3_key}"
    with smart_open(s3_file_uri, "r") as fp:
        page = json.load(fp)

    page_id = page.pop("pageid")
    content = page.pop("content")
    page["uri"] = s3_file_uri
    page["embedding"] = get_embedding(content)

    es_handler.index(INDEX_NAME, body=page, id=page_id)


def lambda_handler(event: Any, _: Any) -> None:
    """
    lambda handler
    """
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(event["Records"][0]["s3"]["object"]["key"], encoding="utf-8")
    try:
        index_page(bucket, key)
    except Exception as e:
        print(e)
        print("Error getting object {} from bucket {}.".format(key, bucket))
        print("Make sure they exist and your bucket is in the same region as this function.")
        raise e


if __name__ == "__main__":
    test_event = {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "stacks-docsdestination32d97be3-f6y6ohczj5zd"},
                    "object": {"key": "wikipages/43758295"},
                }
            }
        ]
    }
    lambda_handler(test_event, None)

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

s3 = boto3.client("s3")

ES_URL = "https://search-semwiki-6yrq325yksanyp2gwbjbk63une.eu-west-1.es.amazonaws.com/"
ES_AUTH = ("semwiki", "SemWiki21!")
es_handler = es.Elasticsearch([ES_URL], http_auth=ES_AUTH, use_ssl=True, verify_certs=False)

index_name = "semwiki"


def get_embedding(text: str) -> List[float]:
    """
    send text to embedding service and return embedding
    """
    service_url = "http://34.252.37.103:8501"
    service_endpoint = f"{service_url}/v1/models/USE_3:predict"
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

    es_handler.index(index_name, body=page, id=page_id)


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
                    "bucket": {"name": "wikireferencing-docsdestination32d97be3-f6y6ohczj5zd"},
                    "object": {"key": "wikipages/43758295"},
                }
            }
        ]
    }
    lambda_handler(test_event, None)

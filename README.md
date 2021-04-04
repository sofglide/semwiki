# Wikipedia Semantic Referencing example


## Description
This is work in progress, many things in the workflow should be improved and 
automated.

This is still functional and it does the following:
* `src/wiki.py` gets random pages from wikipedia, enriches them with metadata
  and uploads them to an s3 bucket. This can be also run using
  ```bash
  python src/scripts.py upload-random-pages -n <number of random pages to upload>
  ```
* `src/lambda_indexer` defines an lambda function that is attached to create
events in the S3 bucket. It sends the page content to the embedding service
and references the document and its embedding in the ElasticSearch cluster
* `universal-sentence-encoder` defines the docker image that is pushed to
ECR and then deployed in ECS. It provides a service that given a text
returns its embedding. It can be used as follows
  ```bash
   curl -XPOST -d '{"instances": ["text 1 to query", "text 2 to query"]}' http://serviceIP:8501/v1/models/USE_3:predict | jq
  ```
* `src/es` is related to the ElasticSearch cluster where the pages are referenced.
It contains modules to create the index, index a document, and search the index
using knn similarity
* `src/api` a sanic server listening on port 8000 with an endpoint `/search` which takes a text
as a query, sends it to the embedding service, takes the returned embedding
  and sends a query to the ElasticSearch index with that embedding. Finally
  it returns the results. To use it, run `src/api/search_server` then
  execute the following command which requests 3 most similar Wikipedia pages
  to the text "beautiful painting":
  ```bash
  curl -XGET -d '{"query": "beautiful painting"}' localhost:8000/search?n=3 | jq
  ```
  This server is also deployed as an AWS service which can be reached through
  ```shell
  curl -XGET -d '{"query": "beautiful painting"}' 52.30.220.81:8000/search\?n=3 | jq
  ```

## Disclaimers
The API service, the embedding service and the ElasticSearch cluster get a new dynamic IP everytime they
are redeployed. Since this is just a prototype it is not necessary to acquire fixed IPs as they are not
free. So, it can happen that the IPs in this document and in the config file may be outdated if
these services have been redeployed without updating the files.

## Initial setup
The setup is not at production grade. However, reading the makefile is not very complicated.

Start by creating the virtual environment with
```shell
make env-create
source .venv/bin/activate
```

## TODO
* automate AWS infrastructure deployment using Makefile and AWS-CDK
* deploy search endpoint in AWS

## ElasticSearch cURL requests (saved here to be used for debugging)
```
GET /_cat/indices/semwiki?v=true&s=index&pretty

GET /semwiki/_settings?pretty

GET /semwiki/_mappings?pretty

GET /semwiki/_stats

GET /semwiki/_doc/19045501

GET /semwiki/_search
{
  "size": 3,
  "_source": ["url", "uri", "title"],
    "query": {
      "function_score": {
        "functions": [{
          "random_score": {
            "seed": "1518707649"
          }
        }
      ]
    }
  }
}
```
# Semantic search service over wikipedia articles using AWS infrastructure

![semantic search](images/wikipedia_semantic_search.svg?raw=true "Wikipedia Semantic Search")

## Description
This is work in progress, many things in the workflow should be improved and 
automated.

This is still functional and it does the following:
* `src/wiki.py` gets random pages from wikipedia, enriches them with metadata
  and uploads them to an s3 bucket. This can be also run using
  ```bash
  python src/scripts.py upload-random-pages -n <NUMBER_OF_RANDOM_PAGES_TO_UPLOAD>
  ```
* `lambda_indexer/` defines a lambda function that is attached to create
events in the S3 bucket. It sends the page content to the embedding service
and references the document and its embedding in the ElasticSearch cluster
* `universal-sentence-encoder` defines the docker image that is pushed to
ECR and then deployed in ECS. It provides a service that given a text
returns its embedding. It can be used as follows
  ```bash
   curl -XPOST -d '{"instances": ["text 1 to query", "text 2 to query"]}' http://<EMBEDDER_IP>:8501/v1/models/USE_3:predict | jq
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
  curl -XGET -d '{"query": "beautiful painting"}' <API_SERVICE_IP>:8000/search\?n=3 | jq
  ```

## Initial setup
The setup is not at production grade. However, reading the makefile is not very complicated.

Start by creating the virtual environment with
```shell
make env-create
source .venv/bin/activate
```

# How to deploy stacks
* package indexing lambda
  ```shell
  make lambda-indexer-package
  ```
* deploy Elasticsearch stack
  ```shell
  make deploy-es
  ```
* in `src/config/config.ini` update `es_url` with Elasticsearch endpoint. This can be obtained with `make echo-elastic-search-endpoint`
* create the index in the cluster
  ```shell
  make create-es-index
  ```
* build and push embedder image
  ```shell
  make docker-embedder-image && make docker-embedder-push
  ```
* deploy embedding stack
   ```shell
   make deploy-embedder
   ```
* check the embedding service
  * Embedder IP can be obtained with `make echo-embedder-ip`
  ```shell
  curl -XPOST -d '{"instances": ["toto", "tata"]}' http://<EMBEDDER_IP>:8501/v1/models/USE_3:predict | jq
  ```
* in `src/config/config.ini` update `public_ip` with embedding service public IP
  * this is a workaround to pass the embedding service container to the indexer
  lambda and the API service. A robust solution would be to assign a load balancer
    with an elastic IP to the embedder serivce, but this would increase the cost
    and the purpose of this repo is only to showcase the semantic search solution.
* package indexing lambda
  ```shell
  make lambda-indexer-package
  ```
* deploy WikiReferencing stack (S3 bucket + Lambda function + S3 Notification)
  ```shell
  make deploy-referencing
  ```
* check the referencing stack by sending a batch of Wikipedia pages, you should find json
files added to the s3 bucket and the corresponding pages indexed in Elasticsearch index `semwiki`
  ```shell
  python src/scripts.py upload-random-pages -n 5
  ```
* list documents in Elasticsearch index
  * Elasticsearch endpoint can be obtained with `make echo-elastic-search-endpoint`
  ```shell
  curl -XGET -u 'semwiki:SemWiki21!' -H 'Content-Type: application/json' \
    -d '{"_source": "title", "query": {"match_all": {}}}' https://<ES_ENDPOINT>/semwiki/_search | jq
  ```
* build and push API image
  ```shell
  make docker-api-image && make docker-api-push
  ```
* deploy API service
  ```shell
  make deploy-api
  ```
* test API service
  * Search API IP can be obtained with `make echo-api-ip`
  ```shell
  curl -XGET -d '{"query": "entertainment"}' http://<API_SERVICE_IP>:8000/search\?n\=3 | \
      jq '.[] | {"title": .title, "url": .url}'
  ```

## Disclaimers
The Elasticsearch service, the embedding service get a new IP everytime their containers
are re-instantiated. This makes it difficult to reach them. We should use a load
balancer with a fixed public IP to overcome this problem, but since the objective
of this project is only to show the main idea of how to implement a semantic search
engine, we do not want to have unnecessary costs related to these additional resources.

Consequently, for now, when the embedder is unreachable (from the indexing lambda or the search service),
their respective code and docker image have to be updated with the new embedder IP.
This happens when the embedder service is killed and re-created.


## ElasticSearch cURL requests (saved here to be used for debugging)
```
GET /_cat/indices?v=true&s=index&pretty

GET /_cat/indices/semwiki?v=true&s=index&pretty

GET /_cat/indices/semwiki?format=json

GET /semwiki

GET /semwiki/_settings

GET /semwiki/_mappings

GET /semwiki/_stats

GET /semwiki/_doc/17793022

DELETE /semwiki/_doc/00000000?routing=shard-1&pretty

GET /semwiki/_doc/53747466?pretty

GET /semwiki/_search
{
  "size": 10,
  "_source": [
    "url",
    "uri",
    "title"
  ],
  "query": {
    "function_score": {
      "functions": [
        {
          "random_score": {
            "seed": "1518707649"
          }
        }
      ]
    }
  }
}

GET /semwiki/_search
{
  "size": 5,
  "query": {
    "function_score": {
      "query": {
        "match_all": {}
      },
      "functions": [
        {
          "random_score": {}
        }
      ]
    }
  }
}

GET /semwiki/_search
{
  "_source": [
    "title"
  ],
  "query": {
    "match_all": {}
  }
}

GET /semwiki/_search
{
  "size": 10,
  "stored_fields": [
    "_id"
  ],
  "_source": [
    "title",
    "url"
  ],
  "query": {
    "match_all": {}
  }
}

POST /semwiki/_delete_by_query
{
  "query": {
    "match_all": {}
  }
}
```

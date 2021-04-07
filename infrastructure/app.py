"""
cdk app
"""
from aws_cdk import core
from stacks.embedder_stack import EmbeddingService
from stacks.es_stack import ElasticSearchCluster
from stacks.s3referencing_stack import S3Referencing
from stacks.search_api_stack import SearchAPIService

app = core.App()

# indexing stack
es_stack = ElasticSearchCluster(app, "ESCluster", env={"region": "eu-west-1"}, description="ElasticSearch cluster")
# embedding stack
embedding_stack = EmbeddingService(
    app, "EmbeddingService", env={"region": "eu-west-1"}, description="Embedding service"
)
# referencing stack
S3Referencing(
    app,
    "WikiReferencing",
    env={"region": "eu-west-1"},
    description="Wiki bucket, indexing lambda and s3 notification",
    elastic_domain=es_stack.elastic_domain,
)
# api stack
SearchAPIService(
    app,
    "SearchAPIService",
    env={"region": "eu-west-1"},
    description="Search API service",
    elastic_domain=es_stack.elastic_domain,
)

app.synth()

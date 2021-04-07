from aws_cdk import core
from stacks.embedder_stack import SearchAPIService
from stacks.es_stack import ElasticSearchCluster
from stacks.s3referencing_stack import S3Referencing

app = core.App()

# referencing stack
S3Referencing(
    app, "WikiReferencing", env={"region": "eu-west-1"}, description="Wiki bucket, indexing lambda and s3 notification"
)
# indexing stack
ElasticSearchCluster(app, "ESCluster", env={"region": "eu-west-1"}, description="ElasticSearch cluster")
# embedding stack
SearchAPIService(app, "EmbeddingService", env={"region": "eu-west-1"}, description="Embedding service")
# api stack
SearchAPIService(app, "SearchAPIService", env={"region": "eu-west-1"}, description="Search API service")

app.synth()
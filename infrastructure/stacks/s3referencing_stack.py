"""
S3 bucket, notification trigger and lambda function
"""
from aws_cdk import aws_elasticsearch as aes
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_notifications as s3n
from aws_cdk import core

from config import config

LAMBDA_PATH = "../lambda_indexer/lambda_indexer.zip"


class S3Referencing(core.Stack):
    """
    S3 bucket, notification trigger and lambda function
    """

    def __init__(
        self,
        scope: core.Construct,
        construct_id: str,
        elastic_domain: aes.Domain,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        indexing_lambda = _lambda.Function(
            self,
            "IndexingHandler",
            runtime=_lambda.Runtime.PYTHON_3_8,
            code=_lambda.Code.asset(LAMBDA_PATH),
            handler="lambda_function.lambda_handler",
            environment={
                "EMBEDDER_IP": config.get_embedder_ip(),
                "ES_URL": elastic_domain.domain_endpoint,
                "ES_USER": config.get_es_credentials()[0],
                "ES_PASSWORD": config.get_es_credentials()[1],
                "INDEX_NAME": config.get_es_index(),
            },
        )
        notification = s3n.LambdaDestination(indexing_lambda)

        block_public_access = s3.BlockPublicAccess(
            block_public_acls=True, block_public_policy=True, ignore_public_acls=True, restrict_public_buckets=True
        )
        bucket = s3.Bucket(
            self, "DocsDestination", block_public_access=block_public_access, removal_policy=core.RemovalPolicy.DESTROY
        )
        bucket.grant_read(indexing_lambda)
        bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            notification,
            s3.NotificationKeyFilter(prefix="wikipages/"),
        )

        core.Tags.of(indexing_lambda).add("system-id", config.get_system_id())
        core.Tags.of(bucket).add("system-id", config.get_system_id())

        core.CfnOutput(self, "S3BucketName", value=bucket.bucket_name)
        core.CfnOutput(self, "IndexingLambdaName", value=indexing_lambda.function_name)

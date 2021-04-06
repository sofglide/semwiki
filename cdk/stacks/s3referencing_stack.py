from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_notifications as s3n
from aws_cdk import core

from config import config

LAMBDA_PATH = "../src/lambda_indexer/lambda_indexer.zip"


class S3Referencing(core.Stack):
    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        indexing_lambda = _lambda.Function(
            self,
            "IndexingHandler",
            runtime=_lambda.Runtime.PYTHON_3_8,
            code=_lambda.Code.asset(LAMBDA_PATH),
            handler="lambda_function.lambda_handler",
        )

        notification = s3n.LambdaDestination(indexing_lambda)

        bucket = s3.Bucket(self, "DocsDestination")
        bucket.grant_read(indexing_lambda)
        bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            notification,
            s3.NotificationKeyFilter(prefix="wikipages/"),
        )

        core.Tags.of(indexing_lambda).add("system-id", config.get_system_id())
        core.Tags.of(bucket).add("system-id", config.get_system_id())

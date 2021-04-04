from aws_cdk import core
from wikireferencing.wikireferencing_stack import WikiReferencingStack

app = core.App()
WikiReferencingStack(
    app, "WikiReferencing", env={"region": "eu-west-1"}, description="Wiki bucket, indexing lambda and s3 notification"
)

app.synth()

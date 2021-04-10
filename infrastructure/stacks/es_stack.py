"""
ElasticSearch Stack
"""
from aws_cdk import aws_elasticsearch as aes
from aws_cdk import aws_iam as iam
from aws_cdk import core

from config import config


class ElasticSearchCluster(core.Stack):
    """
    ElasticSearch Domain
    """

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # elastic policy
        elastic_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "es:*",
            ],
            resources=["*"],
        )
        elastic_policy.add_any_principal()

        self.elastic_domain = aes.Domain(
            self,
            "elastic_domain",
            version=aes.ElasticsearchVersion.V7_9,
            capacity=aes.CapacityConfig(data_node_instance_type="t3.small.elasticsearch", data_nodes=1),
            ebs=aes.EbsOptions(enabled=True, volume_size=10),
            access_policies=[elastic_policy],
            fine_grained_access_control=aes.AdvancedSecurityOptions(
                master_user_name=config.get_es_credentials()[0],
                master_user_password=core.SecretValue(config.get_es_credentials()[1]),
            ),
            zone_awareness=aes.ZoneAwarenessConfig(enabled=False),
            node_to_node_encryption=True,
            encryption_at_rest=aes.EncryptionAtRestOptions(enabled=True),
            enforce_https=True,
            removal_policy=core.RemovalPolicy.DESTROY,
        )

        core.Tags.of(self.elastic_domain).add("system-id", config.get_system_id())

        core.CfnOutput(self, "ESDomainEndpoint", value=self.elastic_domain.domain_endpoint)

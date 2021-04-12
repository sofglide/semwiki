"""
Embedding service stack
"""
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_ecs as ecs
from aws_cdk import core

from config import config

EMBEDDING_REPO_NAME = "semwiki/universal_sentence_encoder_3"
EMBEDDING_IMAGE_TAG = "latest"


class EmbeddingService(core.Stack):
    """
    ECS Embedding Service
    """

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc(self, "EmbeddingVpc", max_azs=1, nat_gateways=0)

        cluster = ecs.Cluster(self, "EmbeddingCluster", vpc=vpc)

        task_definition = ecs.FargateTaskDefinition(self, "EmbeddingTask", cpu=1024, memory_limit_mib=2048)

        ecr_repo = ecr.Repository.from_repository_name(self, "EmbeddingRepo", EMBEDDING_REPO_NAME)
        container_image = ecs.ContainerImage.from_ecr_repository(repository=ecr_repo, tag=EMBEDDING_IMAGE_TAG)
        task_definition.add_container(
            "EmbeddingContainer",
            image=container_image,
            port_mappings=[ecs.PortMapping(container_port=8501, protocol=ecs.Protocol.TCP)],
            memory_reservation_mib=2048,
        )

        embedding_service = ecs.FargateService(
            self,
            "EmbeddingService",
            task_definition=task_definition,
            cluster=cluster,
            assign_public_ip=True,
            desired_count=1,
        )

        embedding_service.connections.security_groups[0].add_ingress_rule(
            peer=ec2.Peer.ipv4("0.0.0.0/0"),
            connection=ec2.Port.tcp(8501),
            description="Allow TF serving REST inbound from VPC",
        )

        core.Tags.of(vpc).add("system-id", config.get_system_id())
        core.Tags.of(cluster).add("system-id", config.get_system_id())
        core.Tags.of(task_definition).add("system-id", config.get_system_id())

        core.CfnOutput(self, "ClusterArn", value=cluster.cluster_arn)

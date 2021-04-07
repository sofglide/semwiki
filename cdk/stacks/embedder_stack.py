from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_ecs as ecs
from aws_cdk import core

from config import config

API_REPO_NAME = "semwiki/wikisemantic-api"
API_IMAGE_TAG = "latest"


class SearchAPIService(core.Stack):
    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc(self, "SearchAPIVpc", max_azs=1)

        cluster = ecs.Cluster(self, "SearchAPICluster", vpc=vpc)

        task_definition = ecs.FargateTaskDefinition(self, "SearchAPITask", cpu=256, memory_limit_mib=512)

        ecr_repo = ecr.Repository.from_repository_name(self, "SearchAPIRepo", API_REPO_NAME)
        container_image = ecs.ContainerImage.from_ecr_repository(repository=ecr_repo, tag=API_IMAGE_TAG)
        task_definition.add_container(
            "SearchAPIContainer",
            image=container_image,
            port_mappings=[ecs.PortMapping(container_port=8000, protocol=ecs.Protocol.TCP)],
            memory_reservation_mib=512,
        )

        fargate_service = ecs.FargateService(
            self,
            "SearchAPIService",
            task_definition=task_definition,
            cluster=cluster,
            assign_public_ip=True,
            desired_count=1,
        )

        fargate_service.connections.security_groups[0].add_ingress_rule(
            peer=ec2.Peer.ipv4("0.0.0.0/0"),
            connection=ec2.Port.tcp(8000),
            description="Allow TF serving REST inbound from VPC"
        )

        core.Tags.of(vpc).add("system-id", config.get_system_id())
        core.Tags.of(cluster).add("system-id", config.get_system_id())
        core.Tags.of(task_definition).add("system-id", config.get_system_id())
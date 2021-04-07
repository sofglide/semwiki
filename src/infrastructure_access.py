"""
utils for indexing lambda
"""
import os
from typing import Dict, List

import boto3

ecs_client = boto3.client("ecs", region_name="eu-west-1")
ec2_resource = boto3.resource("ec2", region_name="eu-west-1")
cfn_client = boto3.client("cloudformation", region_name="eu-west-1")


def get_embedder_ip_from_env() -> str:
    """
    get embedder ip from environment cluster anr
    """
    cluster = os.getenv("EMBEDDER_ARN")
    if cluster is None:
        raise ValueError("Environment variable 'EMBEDDER_ARN' needs to be specified")
    return get_embedder_ip_from_arn(cluster)


def get_embedder_ip_from_arn(cluster: str) -> str:
    """
    get embedder ip from cluster arn
    """
    task = ecs_client.list_tasks(cluster=cluster)["taskArns"][0]

    attachment_details = ecs_client.describe_tasks(cluster=cluster, tasks=[task])["tasks"][0]["attachments"][0][
        "details"
    ]
    eni_id = get_value_from_attachment_details(attachment_details, "networkInterfaceId")
    return ec2_resource.NetworkInterface(eni_id).association_attribute["PublicIp"]


def get_es_endpoint() -> str:
    es_stack_output = cfn_client.describe_stacks(StackName="ESCluster")["Stacks"][0]["Outputs"]
    return get_value_from_cfn_output(es_stack_output, "ESDomainEndpoint")


def get_s3_bucket_name() -> str:
    referencing_stack_output = cfn_client.describe_stacks(StackName="WikiReferencing")["Stacks"][0]["Outputs"]
    return get_value_from_cfn_output(referencing_stack_output, "S3BucketName")


def get_value_from_attachment_details(attachment_details: List[Dict[str, str]], name: str) -> str:
    return next(filter(lambda x: x["name"] == name, attachment_details))["value"]


def get_value_from_cfn_output(cfn_output: List[Dict[str, str]], output_key: str) -> str:
    return next(filter(lambda x: x["OutputKey"] == output_key, cfn_output))["OutputValue"]

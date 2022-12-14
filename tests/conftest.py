# -*- coding: utf-8 -*-

"""Common pytest fixtures for other tests"""

import os

import boto3
import pytest

from moto import mock_ec2


@pytest.fixture(name='aws_credentials', scope="session")
def define_aws_credentials():
    """Mocked AWS Credentials for moto"""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-west-2"


# pylint: disable=W0613
@pytest.fixture(name='aws_ec2_client', scope="session")
def create_aws_ec2_client(aws_credentials):
    """Create EC2 client for other tests"""
    with mock_ec2():
        ec2_client = boto3.client("ec2", region_name="us-east-1")
        yield ec2_client


@pytest.fixture(scope="session")
def aws_ec2_instances(aws_ec2_client):
    """Create basic set of EC2 instances for tests"""
    instances_list = []

    image_id = aws_ec2_client.describe_images()['Images'][0]['ImageId']

    tag_names = ['webserver01', 'appserver01', '', 'NA']
    tag_environments = ['production', 'staging', '', 'NA']
    tag_departments = ['marketing', 'finance', '', 'NA']

    for tag_name in tag_names:
        for tag_environment in tag_environments:
            for tag_department in tag_departments:
                tags_list = []
                if tag_department != 'NA':
                    tags_list.append(
                        {
                            'Key': 'department',
                            'Value': tag_department
                        }
                    )
                if tag_environment != 'NA':
                    tags_list.append(
                        {
                            'Key': 'environment',
                            'Value': tag_environment
                        }
                    )
                if tag_name != 'NA':
                    tags_list.append(
                        {
                            'Key': 'Name',
                            'Value': tag_name
                        }
                    )

                if tags_list:
                    aws_ec2_client.run_instances(
                        ImageId=image_id,
                        InstanceType='t3.small',
                        DryRun=False,
                        MinCount=1,
                        MaxCount=1,
                        TagSpecifications=[
                            {
                                'ResourceType': 'instance',
                                'Tags': tags_list
                            }
                        ]
                    )

    yield instances_list

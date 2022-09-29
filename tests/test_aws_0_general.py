# -*- coding: utf-8 -*-

import boto3
import pytest

from moto import mock_ec2
import sshcld.plugins.aws as aws


def test_aws_parse_filters_no_filters():
    actual_result = aws.parse_filters()
    assert len(actual_result) == 0


def test_aws_parse_filters_incorrect_filters():
    actual_result = aws.parse_filters('test')
    assert len(actual_result) == 0


def test_aws_parse_filters_incorrect_special_filters():
    actual_result = aws.parse_filters('.,#$,(),=+123,4%.,,.')
    assert len(actual_result) == 0


def test_aws_parse_filters_one_filter():
    expected_result = [{'Name': 'tag:environment', 'Values': ['prod']}]
    actual_result = aws.parse_filters(filters='environment=prod')
    assert expected_result == actual_result


def test_aws_parse_filters_multiple_filters():
    expected_result = [{'Name': 'tag:environment', 'Values': ['prod']},
                       {'Name': 'tag:application', 'Values': ['nginx']},
                       {'Name': 'tag:department', 'Values': ['marketing']}]
    actual_result = aws.parse_filters(filters='environment=prod,application=nginx,department=marketing')
    assert expected_result == actual_result


def test_aws_parse_instances_no_instances():
    actual_result = aws.parse_instances()
    assert len(actual_result) == 0


def test_aws_parse_instances_incorrect_list():
    actual_result = aws.parse_instances('test')
    assert len(actual_result) == 0


def test_aws_parse_instances_one_instance(aws_credentials):
    with mock_ec2():
        ec2_client = boto3.client('ec2', region_name='eu-central-1')
        image_id = ec2_client.describe_images()['Images'][0]['ImageId']
        ec2_client.run_instances(ImageId=image_id, InstanceType='t3.small', DryRun=False, MinCount=1, MaxCount=1)
        ec2_resource = boto3.resource('ec2', region_name='eu-central-1')
        instances = ec2_resource.instances.filter(DryRun=False, MaxResults=1000)
        actual_result = aws.parse_instances(instances)
    assert len(actual_result) == 1

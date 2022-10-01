# -*- coding: utf-8 -*-

import pytest

import sshcld.plugins.aws as aws


def test_aws_get_instances_all_instances(aws_ec2_instances):
    """Check that all instances from AWS region are returned"""
    assert len(aws.get_instances(region_name='us-east-1')) == 63


def test_aws_get_instances_no_instances(aws_ec2_instances):
    """Check that no instances are returned from unused AWS region"""
    assert len(aws.get_instances(region_name='us-east-2')) == 0


def test_aws_get_instances_env_tag(aws_ec2_instances):
    """Check that no instances are returned from unused AWS region"""
    assert len(aws.get_instances(region_name='us-east-1',
                                 filters='environment=production')) == 16


def test_aws_get_instances_env_department_tags(aws_ec2_instances):
    """Check that no instances are returned from unused AWS region"""
    assert len(aws.get_instances(region_name='us-east-1',
                                 filters='environment=production,department=finance')) == 4


def test_aws_get_instances_env_department_name_tags(aws_ec2_instances):
    """Check that no instances are returned from unused AWS region"""
    assert len(aws.get_instances(region_name='us-east-1',
                                 filters='environment=production,department=finance,Name=appserver01')) == 1


def test_aws_get_instances_non_existing_tags(aws_ec2_instances):
    """Check that no instances are returned from unused AWS region"""
    assert len(aws.get_instances(region_name='us-east-1',
                                 filters='environment=production,department=finance,Name=appserver01,owner=john')) == 0


def test_aws_get_instances_non_existing_tag_values(aws_ec2_instances):
    """Check that no instances are returned from unused AWS region"""
    assert len(aws.get_instances(region_name='us-east-1',
                                 filters='environment=dev,department=finance')) == 0


def test_aws_get_instances_name_tag(aws_ec2_instances):
    """Check that no instances are returned from unused AWS region"""
    assert len(aws.get_instances(region_name='us-east-1',
                                 filters='Name=webserver01')) == 16


def test_aws_get_instances_instance_id(aws_ec2_instances):
    """Check that no instances are returned from unused AWS region"""
    assert len(aws.get_instances(region_name='us-east-1',
                                 filters='FILTER_INSTANCE_ID=i-123456789')) == 0

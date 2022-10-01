# -*- coding: utf-8 -*-

"""Tests for filters from AWS plugin"""

from sshcld.plugins import aws


# pylint: disable=W0613
def test_aws_get_instances_all_instances(aws_ec2_instances):
    """Check that all instances from AWS region are returned"""
    assert len(aws.get_instances(region_name='us-east-1')) == 63


# pylint: disable=W0613
def test_aws_get_instances_no_instances(aws_ec2_instances):
    """Check that no instances are returned from unused AWS region"""
    assert len(aws.get_instances(region_name='us-east-2')) == 0


# pylint: disable=W0613
def test_aws_get_instances_env_tag(aws_ec2_instances):
    """Check that correct number of instances returned with specific environment tag"""
    assert len(aws.get_instances(region_name='us-east-1',
                                 filters='environment=production')) == 16


# pylint: disable=W0613
def test_aws_get_instances_env_department_tags(aws_ec2_instances):
    """Check that correct number of instances returned with specific environment and department tags"""
    assert len(aws.get_instances(region_name='us-east-1',
                                 filters='environment=production,department=finance')) == 4


# pylint: disable=W0613
def test_aws_get_instances_env_department_name_tags(aws_ec2_instances):
    """Check that correct number of instances returned with specific environment, department and name tags"""
    assert len(aws.get_instances(region_name='us-east-1',
                                 filters='environment=production,department=finance,Name=appserver01')) == 1


# pylint: disable=W0613
def test_aws_get_instances_non_existing_tags(aws_ec2_instances):
    """Check that no instances returned for non-existing tag name"""
    assert len(aws.get_instances(region_name='us-east-1',
                                 filters='environment=production,department=finance,Name=appserver01,owner=john')) == 0


# pylint: disable=W0613
def test_aws_get_instances_non_existing_tag_values(aws_ec2_instances):
    """Check that no instances returned for non-existing tag value"""
    assert len(aws.get_instances(region_name='us-east-1',
                                 filters='environment=dev,department=finance')) == 0


# pylint: disable=W0613
def test_aws_get_instances_name_tag(aws_ec2_instances):
    """Check that correct number of instances returned with specific name tag"""
    assert len(aws.get_instances(region_name='us-east-1',
                                 filters='Name=webserver01')) == 16


# pylint: disable=W0613
def test_aws_get_instances_instance_id(aws_ec2_instances):
    """Check that no instances returned for non-existing ID"""
    assert len(aws.get_instances(region_name='us-east-1',
                                 filters='FILTER_INSTANCE_ID=i-123456789')) == 0

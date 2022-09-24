# -*- coding: utf-8 -*-

import pytest

import sshcld.plugins.aws as aws


def test_aws_get_instances_all_instances(aws_ec2_instances):
    """Check that all instances from AWS region are returned"""
    assert len(aws.get_instances(region_name='us-east-1')) == 80


def test_aws_get_instances_no_instances(aws_ec2_instances):
    """Check that no instances are returned from unused AWS region"""
    assert len(aws.get_instances(region_name='us-east-2')) == 0


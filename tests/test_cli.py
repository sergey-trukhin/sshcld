# -*- coding: utf-8 -*-

import pytest

from sshcld import cli


@pytest.fixture()
def aws_ec2_instance_fake():
    instance = {'instance_id': 'i-123456', 'instance_name': 'nginx', 'private_ip_address': '10.0.0.1',
                'public_ip_address': '1.2.3.4', 'tags': {'environment': 'production', 'department': 'marketing'}}
    yield instance


def test_cli_open_yaml_file_minimal_config():
    actual_result = cli.open_yaml_file(path='sshcld_minimal.yaml')
    expected_result = {'default_cloud': 'aws'}
    assert actual_result == expected_result


def test_cli_open_yaml_file_default_config():
    actual_result = cli.open_yaml_file(path='sshcld_default.yaml')
    expected_result = {'aws_ssm_connection_string': 'aws ssm start-session --target %instance_id%',
                       'printable_tags': ['environment', 'department', 'application'],
                       'ssh_connection_string': 'ssh %private_ip_address%', 'default_cloud': 'aws'}
    assert actual_result == expected_result


def test_cli_load_configs_one_file():
    actual_result = cli.load_configs(default_config_path='sshcld_default.yaml', user_config_path='does_not_exist.yaml')
    expected_result = {'aws_ssm_connection_string': 'aws ssm start-session --target %instance_id%',
                       'printable_tags': ['environment', 'department', 'application'],
                       'ssh_connection_string': 'ssh %private_ip_address%', 'default_cloud': 'aws'}
    assert actual_result == expected_result


def test_cli_load_configs_one_file_and_empty():
    actual_result = cli.load_configs(default_config_path='sshcld_default.yaml', user_config_path='sshcld_empty.yaml')
    expected_result = {'aws_ssm_connection_string': 'aws ssm start-session --target %instance_id%',
                       'printable_tags': ['environment', 'department', 'application'],
                       'ssh_connection_string': 'ssh %private_ip_address%', 'default_cloud': 'aws'}
    assert actual_result == expected_result


def test_cli_load_configs_two_files():
    actual_result = cli.load_configs(default_config_path='sshcld_default.yaml', user_config_path='sshcld_user.yaml')
    expected_result = {'aws_ssm_connection_string': 'aws ssm start-session --target %instance_id%',
                       'printable_tags': ['environment', 'department', 'application'],
                       'ssh_connection_string': 'ssh username@%private_ip_address%', 'default_cloud': 'aws',
                       'test_parameter': 'test_value'}
    assert actual_result == expected_result


def test_cli_replace_variables_no_matches(aws_ec2_instance_fake):
    actual_result = cli.replace_variables(string='ssh username@localhost', instance=aws_ec2_instance_fake)
    expected_result = 'ssh username@localhost'
    assert actual_result == expected_result


def test_cli_replace_variables_one_match(aws_ec2_instance_fake):
    actual_result = cli.replace_variables(string='ssh username@%private_ip_address%', instance=aws_ec2_instance_fake)
    expected_result = 'ssh username@10.0.0.1'
    assert actual_result == expected_result


def test_cli_replace_variables_all_matches(aws_ec2_instance_fake):
    actual_result = cli.replace_variables(string='id=%instance_id%, name=%instance_name%, '
                                                 'private_ip=%private_ip_address%, public_ip=%public_ip_address%',
                                          instance=aws_ec2_instance_fake)
    expected_result = 'id=i-123456, name=nginx, private_ip=10.0.0.1, public_ip=1.2.3.4'
    assert actual_result == expected_result


def test_cli_replace_variables_all_matches_with_tags(aws_ec2_instance_fake):
    actual_result = cli.replace_variables(string='id=%instance_id%, name=%instance_name%, '
                                                 'private_ip=%private_ip_address%, public_ip=%public_ip_address%, '
                                                 'env=%tag_environment%, app=%tag_application%, team=%tag_department%',
                                          instance=aws_ec2_instance_fake)
    expected_result = ('id=i-123456, name=nginx, private_ip=10.0.0.1, public_ip=1.2.3.4, env=production, '
                       'app=%tag_application%, team=marketing')
    assert actual_result == expected_result

# -*- coding: utf-8 -*-

"""Tests for cli.py file"""

import os
from pathlib import Path

import pytest

from sshcld import cli


@pytest.fixture(name='aws_ec2_instance_fake')
def create_aws_ec2_instance_fake():
    """Fake instance that will be reused for different tests"""
    instance = {'instance_id': 'i-123456', 'instance_name': 'nginx', 'instance_state': 'running',
                'region': 'us-east-1', 'private_ip_address': '10.0.0.1', 'public_ip_address': '1.2.3.4',
                'tags': {'environment': 'production', 'department': 'marketing'}}
    yield instance


def test_cli_open_yaml_file_minimal_config():
    """Test that minimal config is parsed correctly"""
    config_path = os.path.join(Path(__file__).parent, 'sshcld_minimal.yaml')
    actual_result = cli.open_yaml_file(path=config_path)
    expected_result = {'default_cloud': 'aws'}
    assert actual_result == expected_result


def test_cli_open_yaml_file_default_config():
    """Test that default config is parsed correctly"""
    config_path = os.path.join(Path(__file__).parent, 'sshcld_default.yaml')
    actual_result = cli.open_yaml_file(path=config_path)
    expected_result = {
        'aws_ssm_connection_string': 'aws ssm start-session --target %instance_id% --profile %cloud_profile%',
        'printable_tags': ['environment', 'department', 'application'],
        'ssh_connection_string': 'ssh %private_ip_address%', 'default_cloud': 'aws', 'cloud_region': 'prod'}
    assert actual_result == expected_result


def test_cli_load_configs_one_file():
    """Test that non-existing config is handled correctly"""
    config_path_default = os.path.join(Path(__file__).parent, 'sshcld_default.yaml')
    config_path_user = os.path.join(Path(__file__).parent, 'does_not_exist.yaml')
    actual_result = cli.load_configs(default_config_path=config_path_default, user_config_path=config_path_user)
    expected_result = {
        'aws_ssm_connection_string': 'aws ssm start-session --target %instance_id% --profile %cloud_profile%',
        'printable_tags': ['environment', 'department', 'application'],
        'ssh_connection_string': 'ssh %private_ip_address%', 'default_cloud': 'aws', 'cloud_region': 'prod'}
    assert actual_result == expected_result


def test_cli_load_configs_one_file_and_empty():
    """Test that empty config is handled correctly"""
    config_path_default = os.path.join(Path(__file__).parent, 'sshcld_default.yaml')
    config_path_user = os.path.join(Path(__file__).parent, 'sshcld_empty.yaml')
    actual_result = cli.load_configs(default_config_path=config_path_default, user_config_path=config_path_user)
    expected_result = {
        'aws_ssm_connection_string': 'aws ssm start-session --target %instance_id% --profile %cloud_profile%',
        'printable_tags': ['environment', 'department', 'application'],
        'ssh_connection_string': 'ssh %private_ip_address%', 'default_cloud': 'aws', 'cloud_region': 'prod'}
    assert actual_result == expected_result


def test_cli_load_configs_two_files():
    """Test that two configs are parsed correctly"""
    config_path_default = os.path.join(Path(__file__).parent, 'sshcld_default.yaml')
    config_path_user = os.path.join(Path(__file__).parent, 'sshcld_user.yaml')
    actual_result = cli.load_configs(default_config_path=config_path_default, user_config_path=config_path_user)
    expected_result = {
        'aws_ssm_connection_string': 'aws ssm start-session --target %instance_id% --profile %cloud_profile%',
        'printable_tags': ['environment', 'department', 'application'],
        'ssh_connection_string': 'ssh username@%private_ip_address%', 'default_cloud': 'aws',
        'test_parameter': 'test_value', 'cloud_region': 'prod'}
    assert actual_result == expected_result


def test_cli_replace_variables_no_matches(aws_ec2_instance_fake):
    """Test that variables replacement works if no matches"""
    actual_result = cli.replace_variables(string='ssh username@localhost', instance=aws_ec2_instance_fake,
                                          app_config={})
    expected_result = 'ssh username@localhost'
    assert actual_result == expected_result


def test_cli_replace_variables_one_match(aws_ec2_instance_fake):
    """Test that variables replacement works if one match"""
    actual_result = cli.replace_variables(string='ssh username@%private_ip_address%', instance=aws_ec2_instance_fake,
                                          app_config={})
    expected_result = 'ssh username@10.0.0.1'
    assert actual_result == expected_result


def test_cli_replace_variables_all_matches(aws_ec2_instance_fake):
    """Test that variables replacement works if all matches"""
    actual_result = cli.replace_variables(string='id=%instance_id%, name=%instance_name%, '
                                                 'private_ip=%private_ip_address%, public_ip=%public_ip_address%',
                                          instance=aws_ec2_instance_fake, app_config={})
    expected_result = 'id=i-123456, name=nginx, private_ip=10.0.0.1, public_ip=1.2.3.4'
    assert actual_result == expected_result


def test_cli_replace_variables_all_matches_with_config(aws_ec2_instance_fake):
    """Test that variables replacement works if all matches including variables from YAML config"""
    actual_result = cli.replace_variables(string='id=%instance_id%, name=%instance_name%, '
                                                 'private_ip=%private_ip_address%, public_ip=%public_ip_address%, '
                                                 'region=%cloud_region%, profile=%cloud_profile%',
                                          instance=aws_ec2_instance_fake,
                                          app_config={'cloud_region': 'us-east-1', 'cloud_profile': 'prod'})
    expected_result = 'id=i-123456, name=nginx, private_ip=10.0.0.1, public_ip=1.2.3.4, region=us-east-1, profile=prod'
    assert actual_result == expected_result


def test_cli_replace_variables_all_matches_with_empty_config(aws_ec2_instance_fake):
    """Test that variables replacement works if all matches including variables from YAML config"""
    actual_result = cli.replace_variables(string='id=%instance_id%, name=%instance_name%, '
                                                 'private_ip=%private_ip_address%, public_ip=%public_ip_address%, '
                                                 'region=%cloud_region%, profile=%cloud_profile%',
                                          instance=aws_ec2_instance_fake, app_config={})
    expected_result = 'id=i-123456, name=nginx, private_ip=10.0.0.1, public_ip=1.2.3.4, region=, profile='
    assert actual_result == expected_result


def test_cli_replace_variables_all_matches_with_tags(aws_ec2_instance_fake):
    """Test that variables replacement works if all matches including tags"""
    actual_result = cli.replace_variables(string='id=%instance_id%, name=%instance_name%, '
                                                 'private_ip=%private_ip_address%, public_ip=%public_ip_address%, '
                                                 'env=%tag_environment%, app=%tag_application%, team=%tag_department%',
                                          instance=aws_ec2_instance_fake, app_config={})
    expected_result = ('id=i-123456, name=nginx, private_ip=10.0.0.1, public_ip=1.2.3.4, env=production, '
                       'app=%tag_application%, team=marketing')
    assert actual_result == expected_result


def test_cli_replace_variables_no_public_ip():
    """Test that variables replacement works if instance doesn't have Public IP attribute"""
    instance = {'instance_id': 'i-123456', 'instance_name': 'nginx', 'instance_state': 'running',
                'private_ip_address': '10.0.0.1', 'tags': {'environment': 'production', 'department': 'marketing'}}
    actual_result = cli.replace_variables(string='ssh username@%public_ip_address%', instance=instance,
                                          app_config={})
    expected_result = 'ssh username@'
    assert actual_result == expected_result


def test_cli_replace_variables_no_tags():
    """Test that variables replacement works if instance doesn't have Public IP attribute"""
    instance = {'instance_id': 'i-123456', 'instance_name': 'nginx', 'instance_state': 'pending',
                'private_ip_address': '10.0.0.1', 'public_ip_address': '1.2.3.4'}
    actual_result = cli.replace_variables(string='ssh username@%tag_department%', instance=instance, app_config={})
    expected_result = 'ssh username@%tag_department%'
    assert actual_result == expected_result


def test_cli_get_cli_args_no_args():
    """Test that CLI arguments are parsed correctly if not defined"""
    actual_result = cli.get_cli_args([])
    expected_result = {'region': None, 'profile': None, 'filter': None, 'name': None, 'id': None,
                       'aws': False, 'azure': False, 'ssh': False, 'ssm': False}
    assert expected_result == actual_result


def test_cli_get_cli_args_region():
    """Test that region from CLI arguments is parsed correctly"""
    actual_result = cli.get_cli_args(['-r', 'eu-central-1'])
    assert actual_result['region'] == 'eu-central-1'


def test_cli_get_cli_args_profile():
    """Test that profile from CLI arguments is parsed correctly"""
    actual_result = cli.get_cli_args(['-p', 'prod'])
    assert actual_result['profile'] == 'prod'


def test_cli_get_cli_args_filter():
    """Test that filter from CLI arguments is parsed correctly"""
    actual_result = cli.get_cli_args(['-f', 'environment=production,department=marketing'])
    assert actual_result['filter'] == 'environment=production,department=marketing'


def test_cli_get_cli_args_name():
    """Test that name from CLI arguments is parsed correctly"""
    actual_result = cli.get_cli_args(['-n', 'webserver01'])
    print(actual_result)
    assert actual_result['name'] == 'webserver01'


def test_cli_get_cli_args_id():
    """Test that ID from CLI arguments is parsed correctly"""
    actual_result = cli.get_cli_args(['-i', 'i-987654321'])
    assert actual_result['id'] == 'i-987654321'


def test_cli_get_cli_args_aws():
    """Test that AWS cloud from CLI arguments is parsed correctly"""
    actual_result = cli.get_cli_args(['--aws'])
    assert actual_result['aws']


def test_cli_get_cli_args_azure():
    """Test that Azure cloud from CLI arguments is parsed correctly"""
    actual_result = cli.get_cli_args(['--azure'])
    assert actual_result['azure']


def test_cli_get_cli_args_ssh():
    """Test that SSH parameter from CLI arguments is parsed correctly"""
    actual_result = cli.get_cli_args(['--ssh'])
    assert actual_result['ssh']


def test_cli_get_cli_args_ssm():
    """Test that SSM parameter from CLI arguments is parsed correctly"""
    actual_result = cli.get_cli_args(['--ssm'])
    assert actual_result['ssm']


def test_cli_get_cli_args_all_args():
    """Test that all CLI arguments are parsed correctly"""
    actual_result = cli.get_cli_args(['-r', 'eu-west-1', '-p', 'prod',
                                      '-f', 'environment=production', '--aws', '--ssh', '--ssm'])
    expected_result = {'region': 'eu-west-1', 'profile': 'prod', 'filter': 'environment=production',
                       'name': None, 'id': None, 'aws': True, 'azure': False, 'ssh': True, 'ssm': True}
    assert expected_result == actual_result


@pytest.mark.parametrize('cli_args, yaml_config, expected_result', [
    ({}, {'default_cloud': 'aws'}, None),
    ({'region': 'eu-central-1'}, {'default_cloud': 'aws'}, 'eu-central-1'),
    ({}, {'cloud_region': 'eu-west-1', 'default_cloud': 'aws'}, 'eu-west-1'),
    ({'region': 'eu-central-1'}, {'cloud_region': 'eu-west-1', 'default_cloud': 'aws'}, 'eu-central-1'),
])
def test_cli_enrich_config_region(cli_args, yaml_config, expected_result):
    """Test that config enrichment works for region"""
    assert cli.enrich_config(cli_args=cli_args, yaml_config=yaml_config)['cloud_region'] == expected_result


@pytest.mark.parametrize('cli_args, yaml_config, expected_result', [
    ({}, {'default_cloud': 'aws'}, None),
    ({'profile': 'prod'}, {'default_cloud': 'aws'}, 'prod'),
    ({}, {'cloud_profile': 'staging', 'default_cloud': 'aws'}, 'staging'),
    ({'profile': 'prod'}, {'cloud_profile': 'staging', 'default_cloud': 'aws'}, 'prod'),
])
def test_cli_enrich_config_profile(cli_args, yaml_config, expected_result):
    """Test that config enrichment works for region"""
    assert cli.enrich_config(cli_args=cli_args, yaml_config=yaml_config)['cloud_profile'] == expected_result


@pytest.mark.parametrize('cli_args, yaml_config, expected_result', [
    ({'aws': False, 'azure': False}, {'default_cloud': 'aws'}, 'aws'),
    ({'aws': True, 'azure': False}, {'default_cloud': 'aws'}, 'aws'),
    ({'aws': False, 'azure': True}, {'default_cloud': 'aws'}, 'azure'),
    ({'aws': False, 'azure': False}, {'default_cloud': 'azure'}, 'azure'),
    ({'aws': True, 'azure': False}, {'default_cloud': 'azure'}, 'aws'),
    ({'aws': False, 'azure': True}, {'default_cloud': 'azure'}, 'azure'),
    ({'aws': True, 'azure': False}, {}, 'aws'),
    ({'aws': False, 'azure': True}, {}, 'azure'),
])
def test_cli_enrich_config_cloud_name(cli_args, yaml_config, expected_result):
    """Test that config enrichment works for cloud name"""
    assert cli.enrich_config(cli_args=cli_args, yaml_config=yaml_config)['default_cloud'] == expected_result


@pytest.mark.parametrize('cli_args, yaml_config, expected_result', [
    ({'ssh': False}, {'default_cloud': 'aws', 'ssh_connection_string_enabled': False}, False),
    ({'ssh': True}, {'default_cloud': 'aws', 'ssh_connection_string_enabled': False}, True),
    ({'ssh': False}, {'default_cloud': 'aws', 'ssh_connection_string_enabled': True}, True),
    ({'ssh': True}, {'default_cloud': 'aws', 'ssh_connection_string_enabled': True}, True),
])
def test_cli_enrich_config_ssh_string(cli_args, yaml_config, expected_result):
    """Test that config enrichment works for SSH string"""
    assert cli.enrich_config(cli_args=cli_args,
                             yaml_config=yaml_config)['ssh_connection_string_enabled'] == expected_result


@pytest.mark.parametrize('cli_args, yaml_config, expected_result', [
    ({'ssm': False}, {'default_cloud': 'aws', 'aws_ssm_connection_string_enabled': False}, False),
    ({'ssm': True}, {'default_cloud': 'aws', 'aws_ssm_connection_string_enabled': False}, True),
    ({'ssm': False}, {'default_cloud': 'aws', 'aws_ssm_connection_string_enabled': True}, True),
    ({'ssm': True}, {'default_cloud': 'aws', 'aws_ssm_connection_string_enabled': True}, True),
])
def test_cli_enrich_config_ssm_string(cli_args, yaml_config, expected_result):
    """Test that config enrichment works for SSM string"""
    assert cli.enrich_config(cli_args=cli_args,
                             yaml_config=yaml_config)['aws_ssm_connection_string_enabled'] == expected_result


@pytest.mark.parametrize('cli_args, yaml_config, expected_result', [
    ({}, {'default_cloud': 'aws'}, None),
    ({'filter': ''}, {'default_cloud': 'aws'}, None),
    ({'filter': 'environment=production'}, {'default_cloud': 'aws'}, 'environment=production'),
    ({'filter': 'environment=production,department=marketing,application=nginx'},
     {'default_cloud': 'aws'}, 'environment=production,department=marketing,application=nginx'),
    ({'filter': 'environment=production'},
     {'default_cloud': 'aws', 'filters': 'environment=staging'}, 'environment=production'),
    ({}, {'default_cloud': 'aws', 'filters': 'environment=staging'}, 'environment=staging'),
    ({}, {'default_cloud': 'aws', 'filters': 'environment=staging,department=hr'}, 'environment=staging,department=hr'),
])
def test_cli_enrich_config_filters(cli_args, yaml_config, expected_result):
    """Test that config enrichment works for filters"""
    assert cli.enrich_config(cli_args=cli_args,
                             yaml_config=yaml_config)['filters'] == expected_result


@pytest.mark.parametrize('cli_args, yaml_config, expected_result', [
    ({}, {'default_cloud': 'aws'}, None),
    ({'name': ''}, {'default_cloud': 'aws'}, None),
    ({'name': 'webserver01'}, {'default_cloud': 'aws'}, 'Name=webserver01'),
])
def test_cli_enrich_config_filters_name(cli_args, yaml_config, expected_result):
    """Test that config enrichment works for name as filter"""
    assert cli.enrich_config(cli_args=cli_args, yaml_config=yaml_config)['filters'] == expected_result


@pytest.mark.parametrize('cli_args, yaml_config, expected_result', [
    ({}, {'default_cloud': 'aws'}, None),
    ({'id': ''}, {'default_cloud': 'aws'}, None),
    ({'id': 'i-123456'}, {'default_cloud': 'aws'}, 'FILTER_INSTANCE_ID=i-123456'),
])
def test_cli_enrich_config_filters_id(cli_args, yaml_config, expected_result):
    """Test that config enrichment works for ID as filter"""
    assert cli.enrich_config(cli_args=cli_args, yaml_config=yaml_config)['filters'] == expected_result


# pylint: disable=W0613
def test_cli_get_cloud_instances_empty_region(aws_ec2_instances):
    """Test that empty region is handled correctly"""
    actual_result = cli.get_cloud_instances(app_config={'default_cloud': 'aws', 'cloud_region': 'us-west-1'})
    assert len(actual_result) == 0


# pylint: disable=W0613
def test_cli_get_cloud_instances_empty_filter(aws_ec2_instances):
    """Test that empty filter is handled correctly"""
    actual_result = cli.get_cloud_instances(app_config={'default_cloud': 'aws', 'cloud_region': 'us-east-1'})
    print(actual_result)
    assert len(actual_result) == 63


# pylint: disable=W0613
def test_cli_get_cloud_instances_simple_filter(aws_ec2_instances):
    """Test that simple filter region is handled correctly"""
    actual_result = cli.get_cloud_instances(app_config={'default_cloud': 'aws', 'cloud_region': 'us-east-1',
                                                        'filters': 'environment=production'})
    assert len(actual_result) == 16


# pylint: disable=W0613
def test_cli_get_cloud_instances_complex_filter(aws_ec2_instances):
    """Test that complex filter is handled correctly"""
    actual_result = cli.get_cloud_instances(app_config={'default_cloud': 'aws', 'cloud_region': 'us-east-1',
                                                        'filters': 'environment=production,department=marketing'})
    assert len(actual_result) == 4


# pylint: disable=W0613
def test_cli_get_cloud_instances_non_existing_filter(aws_ec2_instances):
    """Test that filter for non-existing tags returns no results"""
    actual_result = cli.get_cloud_instances(
        app_config={'default_cloud': 'aws', 'cloud_region': 'us-east-1',
                    'filters': 'environment=production,department=marketing,application=nginx'})
    assert len(actual_result) == 0


def test_cli_enrich_instances_metadata_no_instances():
    """Test that instance metadata enrichment works if no instances"""
    expected_result = []
    actual_result = cli.enrich_instances_metadata(instances=[], app_config={})
    assert actual_result == expected_result


def test_cli_enrich_instances_metadata_no_config(aws_ec2_instance_fake):
    """Test that instance metadata enrichment works if no config"""
    expected_result = [{'instance_id': 'i-123456', 'instance_name': 'nginx', 'instance_state': 'running',
                        'region': 'us-east-1', 'private_ip_address': '10.0.0.1', 'public_ip_address': '1.2.3.4'}]
    actual_result = cli.enrich_instances_metadata(instances=[aws_ec2_instance_fake], app_config={})
    assert actual_result == expected_result


def test_cli_enrich_instances_metadata_ssh_string(aws_ec2_instance_fake):
    """Test that instance metadata enrichment works for SSH string"""
    expected_result = [{'instance_id': 'i-123456', 'instance_name': 'nginx', 'instance_state': 'running',
                        'region': 'us-east-1', 'private_ip_address': '10.0.0.1', 'public_ip_address': '1.2.3.4',
                        'ssh_string': 'ssh 10.0.0.1'}]
    actual_result = cli.enrich_instances_metadata(
        instances=[aws_ec2_instance_fake], app_config={'ssh_connection_string': 'ssh %private_ip_address%',
                                                       'ssh_connection_string_enabled': True})
    assert actual_result == expected_result


def test_cli_enrich_instances_metadata_ssh_ssm_string(aws_ec2_instance_fake):
    """Test that instance metadata enrichment works for SSH and SSM strings"""
    expected_result = [{'instance_id': 'i-123456', 'instance_name': 'nginx', 'instance_state': 'running',
                        'region': 'us-east-1', 'private_ip_address': '10.0.0.1', 'public_ip_address': '1.2.3.4',
                        'ssh_string': 'ssh 10.0.0.1', 'native_client_string': ''}]
    actual_result = cli.enrich_instances_metadata(
        instances=[aws_ec2_instance_fake], app_config={'ssh_connection_string': 'ssh %private_ip_address%',
                                                       'aws_ssm_connection_string': 'ssm %instance_id% %cloud_profile%',
                                                       'cloud_profile': 'prod', 'ssh_connection_string_enabled': True,
                                                       'aws_ssm_connection_string_enabled': True})
    assert actual_result == expected_result


def test_cli_enrich_instances_metadata_ssh_ssm_string_cloud(aws_ec2_instance_fake):
    """Test that instance metadata enrichment works for SSH string and another cloud string"""
    expected_result = [{'instance_id': 'i-123456', 'instance_name': 'nginx', 'instance_state': 'running',
                        'region': 'us-east-1', 'private_ip_address': '10.0.0.1', 'public_ip_address': '1.2.3.4',
                        'ssh_string': 'ssh 10.0.0.1', 'native_client_string': 'ssm i-123456 prod'}]
    actual_result = cli.enrich_instances_metadata(
        instances=[aws_ec2_instance_fake], app_config={'ssh_connection_string': 'ssh %private_ip_address%',
                                                       'aws_ssm_connection_string': 'ssm %instance_id% %cloud_profile%',
                                                       'ssh_connection_string_enabled': True,
                                                       'aws_ssm_connection_string_enabled': True,
                                                       'default_cloud': 'aws', 'cloud_profile': 'prod'})
    assert actual_result == expected_result


def test_cli_enrich_instances_metadata_existing_tags(aws_ec2_instance_fake):
    """Test that instance metadata enrichment works for existing tags"""
    expected_result = [{'instance_id': 'i-123456', 'instance_name': 'nginx', 'instance_state': 'running',
                        'region': 'us-east-1', 'private_ip_address': '10.0.0.1', 'public_ip_address': '1.2.3.4',
                        'ssh_string': 'ssh 10.0.0.1', 'native_client_string': 'ssm i-123456',
                        'environment': 'production', 'department': 'marketing'}]
    actual_result = cli.enrich_instances_metadata(
        instances=[aws_ec2_instance_fake], app_config={'ssh_connection_string': 'ssh %private_ip_address%',
                                                       'aws_ssm_connection_string': 'ssm %instance_id%',
                                                       'default_cloud': 'aws',
                                                       'ssh_connection_string_enabled': True,
                                                       'aws_ssm_connection_string_enabled': True,
                                                       'printable_tags': ['environment', 'department']})
    assert actual_result == expected_result


def test_cli_enrich_instances_metadata_non_existing_tags(aws_ec2_instance_fake):
    """Test that instance metadata enrichment works for non-existing tags"""
    expected_result = [{'instance_id': 'i-123456', 'instance_name': 'nginx', 'instance_state': 'running',
                        'region': 'us-east-1', 'private_ip_address': '10.0.0.1', 'public_ip_address': '1.2.3.4',
                        'ssh_string': 'ssh 10.0.0.1', 'environment': 'production',
                        'department': 'marketing', 'application': ''}]
    actual_result = cli.enrich_instances_metadata(
        instances=[aws_ec2_instance_fake], app_config={'ssh_connection_string': 'ssh %private_ip_address%',
                                                       'aws_ssm_connection_string': 'ssm %instance_id%',
                                                       'default_cloud': 'aws',
                                                       'ssh_connection_string_enabled': True,
                                                       'aws_ssm_connection_string_enabled': False,
                                                       'printable_tags': ['environment', 'department', 'application']})
    assert actual_result == expected_result


def test_cli_generate_table_no_instances():
    """Test that table generation works if no instances"""
    actual_result = cli.generate_table(app_config={'default_cloud': 'aws'})
    assert actual_result == 'No servers found matching your filter'


def test_cli_generate_table_one_instance_aws(aws_ec2_instance_fake):
    """Test that table generation works if one AWS instance"""
    instance = aws_ec2_instance_fake.copy()
    instance['ssh_string'] = 'ssh localhost'
    instance['native_client_string'] = 'ssm localhost'
    actual_result = cli.generate_table(app_config={'default_cloud': 'aws', 'ssh_connection_string_enabled': True,
                                                   'aws_ssm_connection_string_enabled': True}, instances=[instance])
    assert 'SSH Connection' in actual_result and 'SSM Connection' in actual_result and 'i-123456' in actual_result


def test_cli_generate_table_one_instance_aws_region(aws_ec2_instance_fake):
    """Test that table generation works if one AWS instance in specific region"""
    instance = aws_ec2_instance_fake.copy()
    instance['ssh_string'] = 'ssh localhost'
    instance['native_client_string'] = 'ssm localhost'
    actual_result = cli.generate_table(app_config={'default_cloud': 'aws', 'ssh_connection_string_enabled': True,
                                                   'aws_ssm_connection_string_enabled': True}, instances=[instance])
    assert 'SSH Connection' in actual_result and 'us-east-1' in actual_result and 'i-123456' in actual_result


def test_cli_generate_table_one_instance_fake_cloud(aws_ec2_instance_fake):
    """Test that table generation works if one instance of another cloud"""
    instance = aws_ec2_instance_fake.copy()
    instance['ssh_string'] = 'ssh localhost'
    instance['native_client_string'] = 'ssm localhost'
    actual_result = cli.generate_table(app_config={'default_cloud': 'fakecloud', 'ssh_connection_string_enabled': False,
                                                   'aws_ssm_connection_string_enabled': True}, instances=[instance])
    assert 'SSH Connection' not in actual_result and 'Native Cloud Connection' in actual_result

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


def test_cli_get_cli_args_no_args():
    actual_result = cli.get_cli_args([])
    expected_result = {'region': None, 'filter': None, 'aws': False, 'azure': False, 'ssh': False, 'ssm': False}
    assert expected_result == actual_result


def test_cli_get_cli_args_region():
    actual_result = cli.get_cli_args(['-r', 'eu-central-1'])
    assert actual_result['region'] == 'eu-central-1'


def test_cli_get_cli_args_filter():
    actual_result = cli.get_cli_args(['-f', 'environment=production,department=marketing'])
    assert actual_result['filter'] == 'environment=production,department=marketing'


def test_cli_get_cli_args_aws():
    actual_result = cli.get_cli_args(['--aws'])
    assert actual_result['aws']


def test_cli_get_cli_args_azure():
    actual_result = cli.get_cli_args(['--azure'])
    assert actual_result['azure']


def test_cli_get_cli_args_ssh():
    actual_result = cli.get_cli_args(['--ssh'])
    assert actual_result['ssh']


def test_cli_get_cli_args_ssm():
    actual_result = cli.get_cli_args(['--ssm'])
    assert actual_result['ssm']


def test_cli_get_cli_args_all_args():
    actual_result = cli.get_cli_args(['-r', 'eu-west-1', '-f', 'environment=production', '--aws', '--ssh', '--ssm'])
    expected_result = {'region': 'eu-west-1', 'filter': 'environment=production', 'aws': True,
                       'azure': False, 'ssh': True, 'ssm': True}
    assert expected_result == actual_result


@pytest.mark.parametrize('cli_args, yaml_config, expected_result', [
    ({}, {'default_cloud': 'aws'}, None),
    ({'region': 'eu-central-1'}, {'default_cloud': 'aws'}, 'eu-central-1'),
    ({}, {'cloud_region': 'eu-west-1', 'default_cloud': 'aws'}, 'eu-west-1'),
    ({'region': 'eu-central-1'}, {'cloud_region': 'eu-west-1', 'default_cloud': 'aws'}, 'eu-central-1'),
])
def test_cli_enrich_config_region(cli_args, yaml_config, expected_result):
    assert cli.enrich_config(cli_args=cli_args, yaml_config=yaml_config)['cloud_region'] == expected_result


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
    assert cli.enrich_config(cli_args=cli_args, yaml_config=yaml_config)['default_cloud'] == expected_result


@pytest.mark.parametrize('cli_args, yaml_config, expected_result', [
    ({'ssh': False}, {'default_cloud': 'aws', 'ssh_connection_string_enabled': False}, False),
    ({'ssh': True}, {'default_cloud': 'aws', 'ssh_connection_string_enabled': False}, True),
    ({'ssh': False}, {'default_cloud': 'aws', 'ssh_connection_string_enabled': True}, True),
    ({'ssh': True}, {'default_cloud': 'aws', 'ssh_connection_string_enabled': True}, True),
])
def test_cli_enrich_config_ssh_string(cli_args, yaml_config, expected_result):
    assert cli.enrich_config(cli_args=cli_args,
                             yaml_config=yaml_config)['ssh_connection_string_enabled'] == expected_result


@pytest.mark.parametrize('cli_args, yaml_config, expected_result', [
    ({'ssm': False}, {'default_cloud': 'aws', 'aws_ssm_connection_string_enabled': False}, False),
    ({'ssm': True}, {'default_cloud': 'aws', 'aws_ssm_connection_string_enabled': False}, True),
    ({'ssm': False}, {'default_cloud': 'aws', 'aws_ssm_connection_string_enabled': True}, True),
    ({'ssm': True}, {'default_cloud': 'aws', 'aws_ssm_connection_string_enabled': True}, True),
])
def test_cli_enrich_config_ssm_string(cli_args, yaml_config, expected_result):
    assert cli.enrich_config(cli_args=cli_args,
                             yaml_config=yaml_config)['aws_ssm_connection_string_enabled'] == expected_result


@pytest.mark.parametrize('cli_args, yaml_config, expected_result', [
    ({}, {'default_cloud': 'aws'}, None),
    ({'filter': ''}, {'default_cloud': 'aws'}, ''),
    ({'filter': 'environment=production'}, {'default_cloud': 'aws'}, 'environment=production'),
    ({'filter': 'environment=production,department=marketing,application=nginx'},
     {'default_cloud': 'aws'}, 'environment=production,department=marketing,application=nginx'),
])
def test_cli_enrich_config_filters(cli_args, yaml_config, expected_result):
    assert cli.enrich_config(cli_args=cli_args,
                             yaml_config=yaml_config)['filters'] == expected_result


def test_cli_get_cloud_instances_empty_region(aws_ec2_instances):
    actual_result = cli.get_cloud_instances(app_config={'default_cloud': 'aws', 'cloud_region': 'us-west-1'})
    assert len(actual_result) == 0


def test_cli_get_cloud_instances_empty_filter(aws_ec2_instances):
    actual_result = cli.get_cloud_instances(app_config={'default_cloud': 'aws', 'cloud_region': 'us-east-1'})
    print(actual_result)
    assert len(actual_result) == 63


def test_cli_get_cloud_instances_simple_filter(aws_ec2_instances):
    actual_result = cli.get_cloud_instances(app_config={'default_cloud': 'aws', 'cloud_region': 'us-east-1',
                                                        'filters': 'environment=production'})
    assert len(actual_result) == 16


def test_cli_get_cloud_instances_complex_filter(aws_ec2_instances):
    actual_result = cli.get_cloud_instances(app_config={'default_cloud': 'aws', 'cloud_region': 'us-east-1',
                                                        'filters': 'environment=production,department=marketing'})
    assert len(actual_result) == 4


def test_cli_get_cloud_instances_non_existing_filter(aws_ec2_instances):
    actual_result = cli.get_cloud_instances(
        app_config={'default_cloud': 'aws', 'cloud_region': 'us-east-1',
                    'filters': 'environment=production,department=marketing,application=nginx'})
    assert len(actual_result) == 0


def test_cli_enrich_instances_metadata_no_instances():
    expected_result = []
    actual_result = cli.enrich_instances_metadata(instances=[], app_config={})
    assert actual_result == expected_result


def test_cli_enrich_instances_metadata_no_config(aws_ec2_instance_fake):
    expected_result = [{'instance_id': 'i-123456', 'instance_name': 'nginx', 'private_ip_address': '10.0.0.1',
                        'public_ip_address': '1.2.3.4', 'ssh_string': '', 'native_client_string': ''}]
    actual_result = cli.enrich_instances_metadata(instances=[aws_ec2_instance_fake], app_config={})
    assert actual_result == expected_result


def test_cli_enrich_instances_metadata_ssh_string(aws_ec2_instance_fake):
    expected_result = [{'instance_id': 'i-123456', 'instance_name': 'nginx', 'private_ip_address': '10.0.0.1',
                        'public_ip_address': '1.2.3.4', 'ssh_string': 'ssh 10.0.0.1', 'native_client_string': ''}]
    actual_result = cli.enrich_instances_metadata(
        instances=[aws_ec2_instance_fake], app_config={'ssh_connection_string': 'ssh %private_ip_address%'})
    assert actual_result == expected_result


def test_cli_enrich_instances_metadata_ssh_ssm_string(aws_ec2_instance_fake):
    expected_result = [{'instance_id': 'i-123456', 'instance_name': 'nginx', 'private_ip_address': '10.0.0.1',
                        'public_ip_address': '1.2.3.4', 'ssh_string': 'ssh 10.0.0.1', 'native_client_string': ''}]
    actual_result = cli.enrich_instances_metadata(
        instances=[aws_ec2_instance_fake], app_config={'ssh_connection_string': 'ssh %private_ip_address%',
                                                       'aws_ssm_connection_string': 'ssm %instance_id%'})
    assert actual_result == expected_result


def test_cli_enrich_instances_metadata_ssh_ssm_string_cloud(aws_ec2_instance_fake):
    expected_result = [{'instance_id': 'i-123456', 'instance_name': 'nginx', 'private_ip_address': '10.0.0.1',
                        'public_ip_address': '1.2.3.4', 'ssh_string': 'ssh 10.0.0.1',
                        'native_client_string': 'ssm i-123456'}]
    actual_result = cli.enrich_instances_metadata(
        instances=[aws_ec2_instance_fake], app_config={'ssh_connection_string': 'ssh %private_ip_address%',
                                                       'aws_ssm_connection_string': 'ssm %instance_id%',
                                                       'default_cloud': 'aws'})
    assert actual_result == expected_result


def test_cli_enrich_instances_metadata_existing_tags(aws_ec2_instance_fake):
    expected_result = [{'instance_id': 'i-123456', 'instance_name': 'nginx', 'private_ip_address': '10.0.0.1',
                        'public_ip_address': '1.2.3.4', 'ssh_string': 'ssh 10.0.0.1',
                        'native_client_string': 'ssm i-123456', 'environment': 'production',
                        'department': 'marketing'}]
    actual_result = cli.enrich_instances_metadata(
        instances=[aws_ec2_instance_fake], app_config={'ssh_connection_string': 'ssh %private_ip_address%',
                                                       'aws_ssm_connection_string': 'ssm %instance_id%',
                                                       'default_cloud': 'aws',
                                                       'printable_tags': ['environment', 'department']})
    assert actual_result == expected_result


def test_cli_enrich_instances_metadata_non_existing_tags(aws_ec2_instance_fake):
    expected_result = [{'instance_id': 'i-123456', 'instance_name': 'nginx', 'private_ip_address': '10.0.0.1',
                        'public_ip_address': '1.2.3.4', 'ssh_string': 'ssh 10.0.0.1',
                        'native_client_string': 'ssm i-123456', 'environment': 'production',
                        'department': 'marketing', 'application': ''}]
    actual_result = cli.enrich_instances_metadata(
        instances=[aws_ec2_instance_fake], app_config={'ssh_connection_string': 'ssh %private_ip_address%',
                                                       'aws_ssm_connection_string': 'ssm %instance_id%',
                                                       'default_cloud': 'aws',
                                                       'printable_tags': ['environment', 'department', 'application']})
    assert actual_result == expected_result
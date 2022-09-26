# -*- coding: utf-8 -*-

"""sshcld: get cloud servers list for your SSH client"""

import argparse
import os
from pathlib import Path
import sys
from tabulate import tabulate
import yaml

import sshcld.plugins.aws as aws
from sshcld.errors import AwsApiError


def open_yaml_file(path=None):
    """Open YAML configuration file"""

    yaml_content = {}

    if path is None:
        return {}

    try:
        with open(path, 'r') as yamlfile:
            yaml_content = yaml.safe_load(yamlfile)
    except FileNotFoundError:
        print(f'YAML config does not exist: {path}')
    except PermissionError:
        print(f'YAML config has incorrect permissions: {path}')
    except (yaml.scanner.ScannerError, yaml.parser.ParserError, yaml.YAMLError) as error:
        print(f'YAML config is invalid ({path}): {error}')

    return yaml_content


def load_configs(default_config_path=None, user_config_path=None):
    """Combine YAML configurations"""

    if default_config_path is None:
        default_config_path = 'sshcld.yaml'
    default_config = open_yaml_file(path=default_config_path)

    if user_config_path is None:
        user_config_path = os.path.join(Path.home(), 'sshcld.yaml')
    user_config = open_yaml_file(path=user_config_path)

    if default_config and user_config:
        all_configs = {**default_config, **user_config}
    elif default_config:
        all_configs = default_config
    elif user_config:
        all_configs = user_config
    else:
        all_configs = {}

    return all_configs


def replace_variables(string=None, instance=None):
    """Replace variables with real values"""

    variables_to_replace = ['instance_id', 'instance_name', 'private_ip_address', 'public_ip_address']

    if string is None or instance is None:
        return ''

    for variable in variables_to_replace:
        string = string.replace(f'%{variable}%', instance[variable])

    if instance.get('tags', None):
        for tag in instance['tags']:
            string = string.replace(f'%tag_{tag}%', instance['tags'][tag])

    return string


def get_cli_args():
    """Get CLI arguments"""

    arg_parser = argparse.ArgumentParser(description='Get cloud servers list for your SSH client')

    arg_parser.add_argument('-r', '--region', help='Cloud region')
    arg_parser.add_argument('-f', '--filter', help='Filter cloud servers by tags')

    cloud_group = arg_parser.add_mutually_exclusive_group()
    cloud_group.add_argument('--aws', action='store_true', default=False, help='Use AWS cloud')
    cloud_group.add_argument('--azure', action='store_true', default=False, help='Use Azure cloud')  # For future usage

    arg_parser.add_argument('--ssh', action='store_true', default=True, help='Show SSH connection string')
    arg_parser.add_argument('--ssm', action='store_true', default=False, help='Show AWS SSM connection string')

    args = vars(arg_parser.parse_args())

    return args


if __name__ == '__main__':

    cli_args = get_cli_args()

    app_config = load_configs()
    if not app_config:
        print('Configuration cannot be empty. Either default or user-defined configuration file should exist.')
        sys.exit(1)

    if cli_args.get('region'):
        cloud_region = cli_args.get('region')
    else:
        cloud_region = app_config.get('cloud_region')

    if cli_args.get('aws'):
        cloud_name = 'aws'
    elif cli_args.get('azure'):
        cloud_name = 'azure'
    elif app_config.get('default_cloud'):
        cloud_name = app_config.get('default_cloud')
    else:
        print('You should specify cloud provider name (aws, azure)')
        sys.exit(1)

    show_ssh_string = cli_args.get('ssh') or app_config.get('ssh_connection_string_enabled')
    show_ssm_string = cli_args.get('ssm') or app_config.get('aws_ssm_connection_string_enabled')

    filters = cli_args.get('filter', '')

    try:
        instances_list = aws.get_instances(region_name=cloud_region, filters=filters)
    except AwsApiError as error:
        print(error)
    else:
        print(instances_list)

    printable_tags = app_config.get('printable_tags', [])

    cloud_name = app_config.get('default_cloud', 'aws')
    if cloud_name == 'aws':
        native_client_string_param = 'aws_ssm_connection_string'
    else:
        native_client_string_param = 'aws_ssm_connection_string'

    for instance in instances_list:
        ssh_string = replace_variables(string=app_config.get('ssh_connection_string', ''), instance=instance)
        native_client_string = replace_variables(string=app_config.get(native_client_string_param, ''), instance=instance)

        for tag in list(instance['tags'].keys()):
            if tag not in printable_tags:
                del instance['tags'][tag]

        for printable_tag in printable_tags:
            if printable_tag not in instance['tags']:
                instance['tags'][printable_tag] = ''

        for converted_tag in instance['tags']:
            instance[converted_tag] = instance['tags'][converted_tag]

        instance['ssh_string'] = ssh_string
        instance['native_client_string'] = native_client_string

        del instance['tags']

    table_headers = {'instance_id': 'Instance ID', 'instance_name': 'Instance Name',
                     'private_ip_address': 'Private IP', 'public_ip_address': 'Public IP',
                     'ssh_string': 'SSH Connection', 'native_client_string': 'SSM Connection'}


    print()
    print(tabulate(instances_list, headers=table_headers))

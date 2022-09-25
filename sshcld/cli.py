# -*- coding: utf-8 -*-

"""sshcld: get cloud servers list for your SSH client"""

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


app_config = load_configs()
if not app_config:
    print('Configuration cannot be empty. Either default or user-defined configuration file should exist.')
    sys.exit(1)


filters = 'environment=prod,application=nginx'

try:
    instances_list = aws.get_instances(region_name='eu-north-1')
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

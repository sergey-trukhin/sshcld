# -*- coding: utf-8 -*-

"""sshcld: get cloud servers list for your SSH client"""

import argparse
import os
from pathlib import Path
import sys
from tabulate import tabulate
import yaml

from sshcld.plugins import aws
from sshcld.errors import AwsApiError


def open_yaml_file(path=None):
    """Open YAML configuration file"""

    yaml_content = {}

    if path is None:
        return {}

    try:
        with open(path, 'r', encoding='utf-8') as yamlfile:
            yaml_content = yaml.safe_load(yamlfile)
    except FileNotFoundError:
        pass
    except PermissionError:
        print(f'YAML config has incorrect permissions: {path}')
    except (yaml.scanner.ScannerError, yaml.parser.ParserError, yaml.YAMLError) as error:
        print(f'YAML config is invalid ({path}): {error}')

    return yaml_content


def load_configs(default_config_path=None, user_config_path=None):
    """Combine YAML configurations"""

    if default_config_path is None:
        default_config_path = os.path.join(Path(__file__).parent, 'sshcld.yaml')
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


def get_cli_args(argv=None):
    """Get CLI arguments"""

    arg_parser = argparse.ArgumentParser(description='Get cloud servers list for your SSH client')

    arg_parser.add_argument('-r', '--region', help='Cloud region')

    filter_type = arg_parser.add_mutually_exclusive_group()
    filter_type.add_argument('-f', '--filter', help='Filter cloud servers by tags')
    filter_type.add_argument('-n', '--name', help='Filter cloud servers by name')
    filter_type.add_argument('-i', '--id', help='Filter cloud servers by server ID')

    cloud_group = arg_parser.add_mutually_exclusive_group()
    cloud_group.add_argument('--aws', action='store_true', default=False, help='Use AWS cloud')
    cloud_group.add_argument('--azure', action='store_true', default=False, help='Use Azure cloud')  # For future usage

    arg_parser.add_argument('--ssh', action='store_true', default=False, help='Show SSH connection string')
    arg_parser.add_argument('--ssm', action='store_true', default=False, help='Show AWS SSM connection string')

    args = vars(arg_parser.parse_args(argv))

    return args


def enrich_config(cli_args=None, yaml_config=None):
    """Enrich YAML configuration using CLI arguments"""

    if cli_args.get('region'):
        yaml_config['cloud_region'] = cli_args.get('region')
    if not yaml_config.get('cloud_region') or yaml_config.get('cloud_region') == '':
        yaml_config['cloud_region'] = None

    if cli_args.get('aws'):
        yaml_config['default_cloud'] = 'aws'
    elif cli_args.get('azure'):
        yaml_config['default_cloud'] = 'azure'
    if not yaml_config.get('default_cloud'):
        print('You should specify cloud provider name (aws, azure)')
        sys.exit(1)

    yaml_config['ssh_connection_string_enabled'] = (cli_args.get('ssh')
                                                    or yaml_config.get('ssh_connection_string_enabled'))
    yaml_config['aws_ssm_connection_string_enabled'] = (cli_args.get('ssm')
                                                        or yaml_config.get('aws_ssm_connection_string_enabled'))

    if cli_args.get('filter'):
        yaml_config['filters'] = cli_args.get('filter')
    elif cli_args.get('name'):
        yaml_config['filters'] = f'Name={cli_args.get("name")}'
    elif cli_args.get('id'):
        yaml_config['filters'] = f'FILTER_INSTANCE_ID={cli_args.get("id")}'
    else:
        yaml_config['filters'] = None

    return yaml_config


def get_cloud_instances(app_config=None):
    """Get list of cloud servers"""

    if app_config is None:
        print('Configuration cannot be empty')
        sys.exit(1)

    if app_config.get('default_cloud') == 'aws':
        try:
            instances_list = aws.get_instances(region_name=app_config.get('cloud_region'),
                                               filters=app_config.get('filters'))
        except AwsApiError as error:
            print(error)
            sys.exit(1)
    else:
        print('You specified cloud that is not supported at the moment')
        sys.exit(1)

    return instances_list


def enrich_instances_metadata(app_config=None, instances=None):
    """Add more metadata for each instance"""

    if app_config is None:
        print('Configuration cannot be empty')
        sys.exit(1)

    printable_tags = app_config.get('printable_tags', [])

    if app_config.get('default_cloud') == 'aws':
        native_client_string_param = 'aws_ssm_connection_string'
    else:
        native_client_string_param = None

    for instance in instances:
        ssh_string = replace_variables(string=app_config.get('ssh_connection_string', ''), instance=instance)
        native_client_string = replace_variables(string=app_config.get(native_client_string_param, ''),
                                                 instance=instance)

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

    return instances


def generate_table(app_config=None, instances=None):
    """Generate table with list of instances"""

    if app_config is None:
        print('Configuration cannot be empty')
        sys.exit(1)

    if instances is None or not instances:
        return 'No servers found matching your filter'

    if app_config.get('default_cloud') == 'aws':
        native_connection_name = 'SSM Connection'
    else:
        native_connection_name = 'Native Cloud Connection'

    table_headers = {'instance_id': 'Instance ID', 'instance_name': 'Instance Name',
                     'private_ip_address': 'Private IP', 'public_ip_address': 'Public IP',
                     'ssh_string': 'SSH Connection', 'native_client_string': native_connection_name}

    table = tabulate(instances, headers=table_headers)

    return table


def show_instances():
    """Show all found instances"""

    cli_args = get_cli_args()

    app_config = load_configs()
    if not app_config:
        print('Configuration cannot be empty. Either default or user-defined configuration file should exist')
        sys.exit(1)

    app_config = enrich_config(cli_args=cli_args, yaml_config=app_config)

    instances_list = get_cloud_instances(app_config=app_config)
    enriched_instances_list = enrich_instances_metadata(app_config=app_config, instances=instances_list)
    instances_table = generate_table(app_config=app_config, instances=enriched_instances_list)

    print(f'\n{instances_table}\n')


if __name__ == '__main__':
    show_instances()

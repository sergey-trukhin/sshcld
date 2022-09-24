# -*- coding: utf-8 -*-

"""Get list of servers from AWS cloud"""

import botocore
import boto3

from sshcld.errors import AwsApiError


def parse_filters(filters=None):
    """Parse filters defined by user"""

    filters_list = []

    if filters is None:
        return []

    if not isinstance(filters, str):
        return []

    conditions = filters.strip().split(',')

    if conditions:
        for condition in conditions:
            try:
                condition_key, condition_value = condition.strip().split('=')
            except ValueError:
                return []
            else:
                filters_list.append(
                    {
                        'Name': f'tag:{condition_key}',
                        'Values': [condition_value]
                    }
                )

    return filters_list


def parse_instances(instances=None):
    """Parse list of EC2 instances returned by AWS API"""

    instances_list = []

    if instances is None:
        return {}

    try:
        for instance in instances:

            try:
                instance_name = next(tag['Value'] for tag in instance.tags if tag['Key'] == 'Name')
            except (StopIteration, TypeError):
                instance_name = ''
            except AttributeError:
                return {}

            try:
                instances_list.append(
                    {
                        'instance_id': instance.instance_id,
                        'instance_name': instance_name,
                        'private_ip_address': instance.private_ip_address,
                        'public_ip_address': instance.public_ip_address,
                        'tags': instance.tags,
                    }
                )
            except AttributeError:
                instances_list.append(
                    {
                        'instance_id': 'unknown',
                        'instance_name': instance_name,
                        'private_ip_address': 'unknown',
                        'public_ip_address': 'unknown',
                        'tags': [],
                    }
                )

    except botocore.exceptions.ClientError as error:
        try:
            error_message = error.response['Error']['Message']
        except KeyError:
            error_message = error
        raise AwsApiError(error_message)

    return instances_list


def get_instances(region_name='us-east-1', filters=None):
    """Make AWS API call to get list of EC2 instances"""

    filters_list = parse_filters(filters)

    ec2 = boto3.resource('ec2', region_name=region_name)

    instances = ec2.instances.filter(
        Filters=filters_list,
        DryRun=False,
        MaxResults=1000,
    )

    try:
        instances_list = parse_instances(instances)
    except AwsApiError:
        raise

    return instances_list

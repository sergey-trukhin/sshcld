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
                if condition_key == 'FILTER_INSTANCE_ID':
                    filters_list = [condition_value]
                    break

                filters_list.append(
                    {
                        'Name': f'tag:{condition_key}',
                        'Values': [condition_value]
                    }
                )

    return filters_list


def parse_instances(instances=None, region_name='us-east-1'):
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
                tags = {}
                if instance.tags:
                    for tag in instance.tags:
                        tags[tag['Key']] = tag['Value']

                instances_list.append(
                    {
                        'instance_id': instance.instance_id,
                        'instance_name': instance_name,
                        'region': region_name,
                        'instance_state': instance.state.get('Name', 'unknown'),
                        'private_ip_address': instance.private_ip_address,
                        'public_ip_address': instance.public_ip_address,
                        'tags': tags,
                    }
                )
            except AttributeError:
                instances_list.append(
                    {
                        'instance_id': 'unknown',
                        'instance_name': instance_name,
                        'instance_state': 'unknown',
                        'region': region_name,
                        'private_ip_address': 'unknown',
                        'public_ip_address': 'unknown',
                        'tags': [],
                    }
                )

    except (botocore.exceptions.NoCredentialsError, botocore.exceptions.EndpointConnectionError,
            botocore.exceptions.UnauthorizedSSOTokenError) as error:
        print(error)  # error message is not shown without print
        raise AwsApiError(error) from error

    except botocore.exceptions.ClientError as error:
        try:
            error_message = error.response['Error']['Message']
            error_code = error.response['Error']['Code']
            if error_code in ('InvalidInstanceID.NotFound', 'InvalidInstanceID.Malformed'):
                return []
        except KeyError:
            error_message = error
        raise AwsApiError(error_message) from error

    return instances_list


def get_instances(region_name='us-east-1', filters=None, profile_name=None):
    """Make AWS API call to get list of EC2 instances"""

    full_instances_list = []

    filters_list = parse_filters(filters)

    if region_name == 'all':
        try:
            region_session = boto3.Session(profile_name=profile_name)
            region_client = region_session.client('ec2', region_name='us-east-1')
            regions_list = [region.get('RegionName') for region in region_client.describe_regions().get('Regions', [])]
        except botocore.exceptions.NoRegionError as error:
            raise AwsApiError(error) from error
        except botocore.exceptions.ProfileNotFound as error:
            raise AwsApiError(error) from error
    else:
        regions_list = region_name.strip().split(',')

    for region in regions_list:

        try:
            if profile_name is not None and profile_name:
                boto3.setup_default_session(profile_name=profile_name)
            ec2 = boto3.resource('ec2', region_name=region)
        except botocore.exceptions.NoRegionError as error:
            raise AwsApiError(error) from error
        except botocore.exceptions.ProfileNotFound as error:
            raise AwsApiError(error) from error

        if len(filters_list) == 1 and isinstance(filters_list[0], str):
            instances = ec2.instances.filter(
                InstanceIds=filters_list,
                DryRun=False,
            )
        else:
            instances = ec2.instances.filter(
                Filters=filters_list,
                DryRun=False,
                MaxResults=1000,
            )

        try:
            instances_list = parse_instances(instances=instances, region_name=region)
        except AwsApiError as error:
            raise AwsApiError from error

        full_instances_list += instances_list

    return full_instances_list

# -*- coding: utf-8 -*-

import plugin_aws as aws

from errors import AwsApiError

filters = 'environment=prod,application=nginx'

try:
    instances_list = aws.get_instances()
except AwsApiError as error:
    print(error)
else:
    print(instances_list)

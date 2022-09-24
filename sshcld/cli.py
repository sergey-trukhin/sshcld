# -*- coding: utf-8 -*-

"""sshcld: get cloud servers list for your SSH client"""

import sshcld.plugins.aws as aws
from sshcld.errors import AwsApiError

filters = 'environment=prod,application=nginx'

try:
    instances_list = aws.get_instances()
except AwsApiError as error:
    print(error)
else:
    print(instances_list)

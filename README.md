# sshcld
Get cloud servers list for your SSH client

Currently, the tool supports AWS cloud only. Support for other clouds is planned for future releases.

## Installation
```commandline
pip install sshcld
```

## Usage
### Basic usage
Show all cloud servers using default credentials and region
```commandline
sshcld
```

### Other options
```commandline
sshcld -r us-east-1,eu-central-1 -p prod -f department=marketing,application=nginx \
    -n webserver01 -i i-123456789 --aws --azure --ssh --ssm
```
- `-r`, `--region` : specify cloud region or comma-separated list of regions. Optionally, you can use "all" for checking all cloud regions.
- `-p`, `--profile` : specify cloud config profile.
- `-f`, `--filter` : show only cloud servers whose tags match the specified filter. Use comma to separate several tags. Can not be used with `--name` and `--id` options.
- `-n`, `--name` : show only cloud servers matching the specified name. Can not be used with `--filter` and `--id` options.
- `-i`, `--id` : show only cloud servers matching the specified name. Can not be used with `--filter` and `--name` options.
- `--aws` : use AWS cloud. Can not be used with `--azure`.
- `--azure` : use Azure cloud. Can not be used with `--aws`.
- `--ssh` : show SSH connection string.
- `--ssm` : show AWS SSM connection string.
- `-h`, `--help` : show help message and exit.

## Configuration
Create `sshcld.yaml` file in your home directory and override any default parameters
```yaml
---

# What cloud server's tags should be displayed
#printable_tags:
#  - environment
#  - department

# What cloud should be used by default
default_cloud: aws

# Default region to gather cloud servers list
#cloud_region: us-east-1

# Default region to gather cloud servers list (can be one region or comma-separated list of regions)
# Use 'all' to retrieve details from all cloud regions
#cloud_profile: default

# Change if you want to enable/disable SSH connection string column
# Or if you want to change connection string's format
ssh_connection_string_enabled: True
ssh_connection_string: ssh %private_ip_address%

# Change if you want to enable/disable AWS SSM connection string column
# Or if you want to change connection string's format
aws_ssm_connection_string_enabled: False
aws_ssm_connection_string: aws ssm start-session --target %instance_id% --profile %cloud_profile%

# Default filter if "-f" argument is not defined
#filters: application=nginx,department=marketing,environment=prod
```

For `ssh_connection_string` and `aws_ssm_connection_string` parameters you can use placeholders.
- Several other parameters from this YAML file: `%cloud_region%`, `%cloud_profile%`
- Several properties of the cloud server: `%instance_id%`, `%instance_name%`, `%private_ip_address%`, `%public_ip_address%`
- Values of any tags assigned to the cloud server: `%tag_<tag_name>%`

## Development
All tool's code is located in the `sshcld` directory.
In addition, tests for pytest are located in the `tests` directory.

You can test your code locally in a Docker container:
```commandline
cd tests
docker build -t sshcld_tests .
cd ..
docker run -t --rm -v ${PWD}/:/app/ sshcld_tests
```

## Contribution
Your contribution is very welcome. You can help in a variety of different ways:
1. Create your pull request with bug fix or new feature
2. Create an issue reporting any unexpected behavior in asking some new feature
3. Test the tool in real live scenarios and provide your feedback via Issues
4. Update/fix documentation via pull requests

### Bug fixes and new features
It's strongly recommended to include tests for your changes to increase chances for the pull request to be reviewed and merged.

### Issues
Please use the following format for reporting bugs:
```text
**Type**: bug
**Version**: X.Y.Z
**OS**: <OS version>
**Python**: X.Y.Z

**Prerequisites**:
1. This should be enabled
2. That should be disabled
3. And one more prerequisite

**Steps to reproduce**:
1. Do something
2. Do something else
3. Check results

**Expected results**:
3. Results should contain something

**Actual results**:
3. Error message:
<paste complete error message here>

**Additional details**:
Anything else you want to add that may help to fix the issue.
```

Please use the following format for asking new features:
```text
**Type**: feature request

**Feature description**:
Add your detailed explanation about desired feature. You can include as much details as you want.

Well explained features have more chances to be implemented.
```

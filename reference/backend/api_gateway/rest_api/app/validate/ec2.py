# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import re
import boto3


def validate_instance_id(id:str, *, raise_exc:bool=False) -> bool:
    """ validates instance id pattern """
    # https://docs.aws.amazon.com/systems-manager/latest/APIReference/API_InstanceInformation.html
    pattern = "(^i-(\w{8}|\w{17})$)|(^mi-\w{17}$)"
    results = re.match(pattern, id)
    if not results and raise_exc:
        raise ValueError("Instance Id not valid")
    return results is not None


def validate_keypair_name(name:str, *, ec2_client=None, raise_exc:bool=False, required:bool=False) -> bool:
    """ validates a keypair name by checking AWS """
    if not name:
        return not required
    if not ec2_client:
        ec2_client = boto3.client('ec2')
    names = [r['KeyName'] for r in ec2_client.describe_key_pairs(KeyNames=[name])['KeyPairs']]
    valid = name in names
    if raise_exc and not valid:
        raise ValueError('Key Pair name not valid')
    return valid


def validate_ami_name(name:str, *, raise_exc:bool=False) -> bool:
    """ validates ami name pattern """
    pattern = "(^ami-\w{17}$)"
    results = re.match(pattern, name)
    if not results and raise_exc:
        raise ValueError("AMI Name not valid")
    return results is not None


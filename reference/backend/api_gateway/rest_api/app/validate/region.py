# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import re
import boto3


def validate_region_name(region_name, *, raise_exc:bool=False):
    """Provided region_name must be a valid host label."""
    if region_name is None:
        return
    valid_host_label = re.compile(r'^(?![0-9]+$)(?!-)[a-zA-Z0-9-]{,63}(?<!-)$')
    valid = valid_host_label.match(region_name)
    if not valid and raise_exc:
        raise ValueError('Invalid region name')
    return valid 


def validate_region_exists(name:str, *, ec2_client=None, raise_exc:bool=False) -> bool:
    if not validate_region_name(name, raise_exc=raise_exc):
        return False

    if not ec2_client:
        ec2_client = boto3.client('ec2')
    names = [r['RegionName'] for r in ec2_client.describe_regions()['Regions']]
    valid = name in names
    if raise_exc and not valid:
        raise ValueError('Region not valid')
    return valid

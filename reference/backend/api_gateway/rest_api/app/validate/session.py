# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import re
import traceback
from globalreview.instances import has_instance_type
from .region import validate_region_name


def validate_session_id(id:str) -> bool:
    # session id is a ksuid (hex str)
    pattern = "(^[0-9a-f]{40}$)"
    results = re.match(pattern, id)
    return results is not None


def validate_resolution(width, height, *, raise_exc:bool=False):
    if not isinstance(width, int) or not isinstance(height, int):
        if raise_exc:
            raise ValueError('Resolution not correct type')
        return False
    if width < 320 or width > 8192 or height < 160 or height > 8192:
        if raise_exc:
            raise ValueError('Resolution not within bounds')
        return False
    return True


def validate_instance_type(instance_type:str, region_name:str, *, raise_exc:bool=False):
    if not validate_region_name(region_name, raise_exc=raise_exc):
        return False
    try:
        results = has_instance_type(instance_type, region_name)
    except:
        traceback.print_exc()
        results = False

    if not results and raise_exc:
        raise ValueError(f'Instance type {instance_type} not available in {region_name} region')
    return results


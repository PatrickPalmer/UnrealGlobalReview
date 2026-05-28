# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

def validate_bool(value, *, raise_exc:bool=False, var:str="parameter"):
    if not isinstance(value, bool):
        if raise_exc:
            raise ValueError(f'Expected bool for {var}')
        return False
    return True

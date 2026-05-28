# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import json
from typing import Any

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi_cognito import CognitoToken
import boto3 


router = APIRouter()

@router.get("/keypairs")
async def get_keypairs() -> Any:

    print(f"endpoint: GET /keypairs")

    ec2_client = boto3.client('ec2')

    keypairs = []
    response = ec2_client.describe_key_pairs()
    if 'KeyPairs' in response:
        keypairs = response['KeyPairs']

    return { 'keypair': keypairs }


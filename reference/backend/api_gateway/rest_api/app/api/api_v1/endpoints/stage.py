# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import json
from typing import Any

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi_cognito import CognitoToken
import boto3 


stage_table_name = json.loads(os.environ.get("DYNAMODB_TABLES"))['stage']

router = APIRouter()

@router.get("/stages")
async def get_stages() -> Any:

    print(f"endpoint: GET /stages")

    dynamodb = boto3.resource('dynamodb') 

    stages = dynamodb.Table(stage_table_name).scan().get('Items', [])

    return { 'stage': stages }


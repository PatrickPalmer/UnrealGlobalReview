# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import json
from typing import Any
import operator

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi_cognito import CognitoToken
import boto3


router = APIRouter()

@router.get("/config/region")
async def get_region() -> Any:

    print(f"endpoint: GET /config/region")

    return { 'region': os.environ.get('AWS_REGION') }


@router.get("/config/regions/installed")
async def get_region_installed() -> Any:

    print(f"endpoint: GET /config/region")

    return { 'region': os.environ.get('AWS_REGION') }


@router.get("/config/regions/available")
async def get_region_available() -> Any:

    print(f"endpoint: GET /config/regions/available")

    available = []

    ec2 = boto3.client("ec2")
    ec2_responses = ec2.describe_regions()
    ssm_client = boto3.client('ssm')
    for resp in ec2_responses['Regions']:
        region_id = resp['RegionName']
                     
        tmp = '/aws/service/global-infrastructure/regions/%s/longName' % region_id
        ssm_response = ssm_client.get_parameter(Name = tmp)
        region_name = ssm_response['Parameter']['Value'] 

        tmp = '/aws/service/global-infrastructure/regions/%s/geolocationRegion' % region_id
        ssm_response = ssm_client.get_parameter(Name = tmp)
        geolocation_region = ssm_response['Parameter']['Value'] 

        tmp = '/aws/service/global-infrastructure/regions/%s/geolocationCountry' % region_id
        ssm_response = ssm_client.get_parameter(Name = tmp)
        geolocation_country = ssm_response['Parameter']['Value'] 

        available.append({
            "RegionId": region_id,
            "RegionName": region_name,
            "GeolocationRegion": geolocation_region,
            "GeolocationCountry": geolocation_country,
        })

    sorted_list = sorted(available, key=operator.itemgetter('RegionId'))

    return { 'region': sorted_list }


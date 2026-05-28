# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import json
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi_cognito import CognitoToken
import globalreview.instances
from app.validate.region import validate_region_name
from app.validate.ec2 import validate_instance_id
import boto3 


stage_table_name = json.loads(os.environ.get("DYNAMODB_TABLES"))['stage']

router = APIRouter()

@router.get("/instances/{region}")
async def get_instances(
    region: str,
    all: Optional[bool] = Query(False, description="list all instances in region")
) -> Any:

    print(f"endpoint: GET /instances/{region}")


    if region:
        if not validate_region_name(region):
            raise HTTPException(status_code=400, detail="Region not valid")

        regions = { region }
    else:
        regions = set()
        regions.add(os.environ.get('AWS_REGION'))
    
        dynamodb = boto3.resource('dynamodb') 
        stages = dynamodb.Table(stage_table_name).scan().get('Items', [])

        for s in stages:
            regions.add(s['DestinationRegion'])

    only_global_review_tagged = not all

    instances = []
    for r in regions:
       instances.extend(globalreview.instances.get_instances_running_in_region_as_dict(r, only_global_review_tagged))

    return { 'instance': instances }


@router.get("/instances/{region}/{instance_id}")
async def get_instance(    
    region: str,
    instance_id: str
) -> Any:
    
    print(f"endpoint: GET /instances/{region}/{instance_id}")

    if not validate_region_name(region):
        raise HTTPException(status_code=400, detail="Region not valid")
    if not validate_instance_id(instance_id):
        raise HTTPException(status_code=400, detail="Instance Id not valid")

    instances = globalreview.instances.get_instances_running_in_region_as_dict(region, False)

    for instance in instances:
        if instance['InstanceId'] == instance_id:
            return { 'instance': instance }

    raise HTTPException( status_code=404, detail="Instance not found")



@router.put("/instances/{region}/{instance_id}/termination")
async def terminate_instance(    
    region: str,
    instance_id: str
) -> Any:

    print(f"endpoint: PUT /instances/{region}/{instance_id}/termination")

    if not validate_region_name(region):
        raise HTTPException(status_code=400, detail="Region not valid")
    if not validate_instance_id(instance_id):
        raise HTTPException(status_code=400, detail="Instance Id not valid")
    
    instances = globalreview.instances.get_instances_running_in_region_as_dict(region, False)

    instance = None
    for i in instances:
        if i['InstanceId'] == instance_id:
            instance = i

    if not instance:
        raise HTTPException( status_code=404, detail="Instance not found")

    try:
        success = globalreview.terminate.terminate_instance(region, instance_id=instance_id, session_id=None, verbose=False)
    except:
        success = False

    return { 'instance': instance, 'success': success }



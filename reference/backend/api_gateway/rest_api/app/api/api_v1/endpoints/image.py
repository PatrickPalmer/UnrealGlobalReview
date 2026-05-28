# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import json
from datetime import datetime
import traceback
from pprint import pprint
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi_cognito import CognitoToken
from app.validate.ec2 import validate_ami_name
import boto3 
from boto3.dynamodb.conditions import Key
from globalreview.cwprint import cwprint_exc, cwprint


# dynamo image table name
image_table_name = json.loads(os.environ.get("DYNAMODB_TABLES"))['image']

router = APIRouter()

@router.get("/images")
async def get_images(
    all: Optional[bool] = Query(False, description="list active and inactive images")
) -> Any:

    print(f"endpoint: GET /images")

    dynamodb = boto3.resource('dynamodb') 

    images = dynamodb.Table(image_table_name).scan().get('Items', [])
    if not all:
        # only show active images 
        # FUTURE: filter in dynamodb
        images = [i for i in images if i['Active']]

    return { 'image': images }


@router.get("/images/{image_id}")
async def get_image(    
    image_id: str
) -> Any:
    
    print(f"endpoint: GET /images/{image_id}")

    if not validate_ami_name(image_id):
        raise HTTPException(status_code=400, detail="Image not valid")

    dynamodb = boto3.resource('dynamodb')
    images = dynamodb.Table(image_table_name) 

    try:
        image = images.query(KeyConditionExpression=Key('Ami').eq(image_id))['Items'][0]
    except:
        raise HTTPException( status_code=404, detail="Image not found")
    
    return { 'image': image }


@router.post("/images")
async def create_image(
    payload: dict = Body(...)
) -> Any:

    print(f"endpoint: POST /images")
    cwprint(payload)

    dynamodb = boto3.resource('dynamodb')
    images = dynamodb.Table(image_table_name)
   
    now = datetime.now()
    isonow = now.strftime('%Y-%m-%dT%H:%M:%S%z')

    image = {
        "Active": True,
        'CreateTime': isonow,
        'UpdateTime': isonow,
        'Region': os.environ.get('AWS_REGION'),
    }

    try:
        image['Ami'] = payload['Ami']
        validate_ami_name(image['Ami'], raise_exc=True)

        image['Name'] = payload['Name'] 
        image['Description'] = payload['Description'] if 'Description' in payload else ''
        image['UnrealInstallDir'] = payload['UnrealInstallDir'] 
        image['Type'] = payload['Type'] if 'Type' in payload else 'Windows'
    except:
        raise HTTPException(status_code=400, detail="Image not complete")

    # validate unreal install dir -- forward slashes, no end slash
    image['UnrealInstallDir'] = image['UnrealInstallDir'].replace('\\', '/')
    if image['UnrealInstallDir'].endswith('/'):
        image['UnrealInstallDir'] = image['UnrealInstallDir'][:-1]

    images.put_item(Item=image)

    return { 'image': image }


@router.put("/images/{image_id}")
async def update_image(
    image_id: str,
    payload: dict = Body(...)
) -> Any:
    
    print(f"endpoint: PUT /images/{image_id}")

    if not validate_ami_name(image_id):
        raise HTTPException(status_code=400, detail="Image not valid")

    dynamodb = boto3.resource('dynamodb')
    images = dynamodb.Table(image_table_name)
   
    now = datetime.now()
    isonow = now.strftime('%Y-%m-%dT%H:%M:%S%z')

    expr = ["UpdateTime=:u"]
    names = { "#UpdateTime" : "UpdateTime"}
    values = { ':u': isonow }

    for idx,param in enumerate(['Active', 'Name', 'Description', 'UnrealInstallDir']):
        if param in payload:
            expr.append(f"#{param}=:{idx+1}")
            names[f"#{param}"] = param
            values[f':{idx+1}'] = payload[param]

    response = images.update_item(
        Key={'Ami': image_id},
        UpdateExpression='set ' + ','.join(expr),
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=values,
        ReturnValues="UPDATED_NEW"
    )

    pprint(response)
    return { 'image': {
        'Id': image_id,
        'UpdateTime': isonow,
    }}
    


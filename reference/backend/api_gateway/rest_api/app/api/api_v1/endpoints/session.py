# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
from datetime import datetime, timedelta
import traceback
import json
from pprint import pprint
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi_cognito import CognitoToken
import boto3 
from boto3.dynamodb.conditions import Key
from ksuid import ksuid
import isodate
import globalreview.log
import globalreview.terminate
from globalreview.cwprint import cwprint_exc, cwprint

from app.validate.ec2 import validate_keypair_name
from app.validate.region import validate_region_exists
from app.validate.type import validate_bool
from app.validate.session import (
    validate_session_id, 
    validate_resolution,
    validate_instance_type,
)


# dynamo session table name
session_table_name = json.loads(os.environ.get("DYNAMODB_TABLES"))['session']
image_table_name = json.loads(os.environ.get("DYNAMODB_TABLES"))['image']

router = APIRouter()

@router.get("/sessions")
async def get_sessions(
    all: Optional[bool] = Query(False, description="list active and inactive sessions")
) -> Any:

    print(f"endpoint: GET /sessions")

    dynamodb = boto3.resource('dynamodb') 

    sessions = dynamodb.Table(session_table_name).scan().get('Items', [])
    if not all:
        # only show active sessions and those that end in less than 12 hours after end time
        # FUTURE: filter in dynamodb
        window = datetime.now() - timedelta(hours=12)
        isowindow = window.strftime('%Y-%m-%dT%H:%M:%S%z')
        sessions = [s for s in sessions if s['Active'] and s['EndTime'] > isowindow]

    return { 'session': sessions }


@router.get("/sessions/{session_id}")
async def get_session(    
    session_id: str
) -> Any:
    
    print(f"endpoint: GET /sessions/{session_id}")

    dynamodb = boto3.resource('dynamodb')
    sessions = dynamodb.Table(session_table_name) 

    try:
        session = sessions.query(KeyConditionExpression=Key('Id').eq(session_id))['Items'][0]
    except:
        raise HTTPException( status_code=404, detail="Session not found")
    
    return { 'session': session }


@router.get("/sessions/{session_id}/logs")
async def get_session_logs(    
    session_id: str
) -> Any:

    print(f"endpoint: GET /sessions/{session_id}/logs")

    logs = globalreview.log.get_log_entries(session_id)
    
    return { 'log': logs }


@router.get("/sessions/{session_id}/status")
async def get_session_status(    
    session_id: str
) -> Any:
    """
    results: 'UNKNOWN'|'RUNNING'|'TERMINATED'|'FAILED'|'TIMED_OUT'|'ABORTED'|'STARTING'|'STOPPED'
    """

    print(f"endpoint: GET /sessions/{session_id}/status")

    if not validate_session_id(session_id):
        raise HTTPException(status_code=400, detail="Session Id not valid")

    # get session
    dynamodb = boto3.resource('dynamodb')
    sessions = dynamodb.Table(session_table_name) 

    try:
        session = sessions.query(KeyConditionExpression=Key('Id').eq(session_id))['Items'][0]
    except:
        raise HTTPException( status_code=404, detail="Session not found")

    # get step function status 
    account_id = boto3.client('sts').get_caller_identity()["Account"]

    aws_region = os.environ.get('AWS_REGION')
    aws_partition = os.environ.get('AWS_PARTITION', 'aws')
    name = os.environ.get('STEPFN_SCHEDULE_SESSION_NAME')
    arn = f'arn:{aws_partition}:states:{aws_region}:{account_id}:execution:{name}:{name}-{session_id}'
    try:
        sf_client = boto3.client('stepfunctions')
        resp = sf_client.describe_execution(executionArn=arn)
        process_status = resp['status']
    except:
        cwprint_exc("Get Session Status")
        process_status = 'MISSING'
    
    if process_status == 'RUNNING':
        process_status = "STARTING"
    elif process_status == "SUCCEEDED" or process_status == "MISSING":
        # check if process is running
        if session['InstanceId']:
            ec2_client = boto3.client('ec2', region_name=session['Region'])
            try:
                response = ec2_client.describe_instances(InstanceIds=[ session['InstanceId'] ])
                instances = response['Reservations'][0]['Instances']
            except Exception as e:
                cwprint_exc(f"Describing Instances ({session['InstanceId']}) for Status")
                instances = []
            
            if len(instances) == 0:
                process_status = "MISSING"
            else:
                state = instances[0]['State']['Name']
                if state in ["running", "pending"]:
                    process_status = "RUNNING"
                elif state in ["stopping", "stopped"]:
                    process_status = "STOPPED"
                else:
                    process_status = "TERMINATED"
        else:
            process_status = "UNKNOWN"


    return { 'status': process_status }


@router.put("/sessions/{session_id}/termination")
async def terminate_session(    
    session_id: str
) -> Any:

    print(f"endpoint: PUT /sessions/{session_id}/termination")

    if not validate_session_id(session_id):
        raise HTTPException(status_code=400, detail="Session Id not valid")

    dynamodb = boto3.resource('dynamodb')
    sessions = dynamodb.Table(session_table_name) 

    try:
        session = sessions.query(KeyConditionExpression=Key('Id').eq(session_id))['Items'][0]
    except:
        raise HTTPException( status_code=404, detail="Session not found")

    if not session['InstanceId']:
        raise HTTPException( status_code=400, detail="Session not instanced")

    try:
        success = globalreview.terminate.terminate_instance(session['Region'], instance_id=session['InstanceId'], session_id=session_id)
    except:
        success = False

    if success:
        globalreview.log.log_entry(session_id, f"Session Terminated ({session['InstanceId']}).")
    else:
        globalreview.log.log_entry(session_id, f"ERROR: Session Termination failed ({session['InstanceId']}).")

    return { 'session': session, 'success': success }


@router.post("/sessions")
async def create_session(
    payload: dict = Body(...)
) -> Any:
    
    print(f"endpoint: POST /sessions")
    cwprint(payload)

    dynamodb = boto3.resource('dynamodb')
    sessions = dynamodb.Table(session_table_name)
   
    now = datetime.now()
    isonow = now.strftime('%Y-%m-%dT%H:%M:%SZ')

    session = {
        "Active": True,
        'Id': f'{ksuid()}',
        'CreateTime': isonow,
        'UpdateTime': isonow,
        'PublicIpAddress': None,
        'PublicDnsName': None,
        'InstanceId': None,
        'SessionUrl': None,
    }

    try:
        session['Ami'] = payload['Ami']
    except:
        cwprint_exc("Create Session: Missing AMI name")
        raise HTTPException(status_code=400, detail=f"Session not complete (field Ami)")

    dynamodb = boto3.resource('dynamodb')
    images = dynamodb.Table(image_table_name) 

    try:
        image = images.query(KeyConditionExpression=Key('Ami').eq(session['Ami']))['Items'][0]
    except:
        raise HTTPException( status_code=404, detail="AMI Image not found")
    
    try:
        session['Region'] = payload['Region']
        validate_region_exists(session['Region'], raise_exc=True)

        session['InstanceType'] = payload['InstanceType']
        validate_instance_type(session['InstanceType'], session['Region'], raise_exc=True)

        session['Duration'] = payload['Duration'] if 'Duration' in payload else 'PT12H'
        dur = isodate.parse_duration(session['Duration'])

        session['StartTime'] = isonow
        session['EndTime'] = (now + dur).strftime('%Y-%m-%dT%H:%M:%SZ')

        session['Name'] = payload['Name'] if 'Name' in payload else ''
        session['Description'] = payload['Description'] if 'Description' in payload else ''

        session['KeyName'] = payload['KeyName'] if 'KeyName' in payload else None
        validate_keypair_name(session['KeyName'])

        session['UnrealProject'] = payload['UnrealProject']
        session['UnrealLevelName'] = payload['UnrealLevelName']

        session['PerforceStream'] = payload['PerforceStream']

        session['RenderWidth'] = payload['RenderWidth'] if 'RenderWidth' in payload else 1920
        session['RenderHeight'] = payload['RenderHeight'] if 'RenderHeight' in payload else 1080
        validate_resolution(session['RenderWidth'], session['RenderHeight'], raise_exc=True)

        session['PixelStreamHMD'] = payload['PixelStreamHMD'] if 'PixelStreamHMD' in payload else False
        validate_bool(session['PixelStreamHMD'], raise_exc=True, var="Pixel Stream HMD")

        session['GameMode'] = payload['GameMode'] if 'GameMode' in payload else True
        validate_bool(session['GameMode'], raise_exc=True, var="Game Mode")

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

    # validate
    required = ['Ami', 'Region', 'InstanceType', 'UnrealProject', 'UnrealLevelName', 'PerforceStream']
    for req in required:
        if not session[req]:
            raise HTTPException(status_code=400, detail=f"Session not complete (field {req})")
            
    # Perforce credentials
    perforce = {}
    try:
        perforce['Port'] = payload['PerforcePort']
        perforce['User'] = payload['PerforceUser']
        perforce['Password'] = payload['PerforcePassword']
    except:
        perforce = None


    if not perforce:
        raise HTTPException(status_code=400, detail="Perforce Credentials not complete")

    sessions.put_item(Item=session)

    # additional fields for scheduled session
    session['AmiName'] = image['Name']
    session['UnrealInstallDir'] = image['UnrealInstallDir']

    schedule_session(session, perforce)

    return { 'session': session }


def schedule_session(session, perforce):
    sfn_client = boto3.client('stepfunctions')

    input = {
        'Ami': session['Ami'],
        'Name': session['Name'],
        'AmiName': session['AmiName'],
        'DestinationRegion': session['Region'],
        'InstanceType': session['InstanceType'],
        'SessionId': session['Id'],
        'StartTime': session['StartTime'],
        'EndTime': session['EndTime'],
        'Duration': session['Duration'],
        'PerforceStream': session['PerforceStream'],
        'UnrealProject': session['UnrealProject'],
        'UnrealLevelName': session['UnrealLevelName'],
        'UnrealInstallDir': session['UnrealInstallDir'],
        'KeyName': session['KeyName'],
        'S3Bucket': os.environ.get('CONTENT_BUCKET_NAME'),
        'S3Prefix': f"Unreal/Projects/{session['Id']}/",
        'SessionRoleArn': os.environ.get('SESSION_ROLE_ARN'),               
        'SessionRoleName': os.environ.get('SESSION_ROLE_NAME'),
        'RenderWidth': session['RenderWidth'],
        'RenderHeight': session['RenderHeight'],
        'PixelStreamHMD': session['PixelStreamHMD'],
        'GameMode': session['GameMode'],
    }    

    # write Perforce credentials to Parameter Store
    ssm_client = boto3.client("ssm")
    try:
        ssm_client.put_parameter(Name=f"/GlobalReview/Perforce/{session['Id']}",
                                 Value=json.dumps(perforce),
                                 Type="SecureString")
    except Exception as e:
        traceback.print_exc()
        raise e
    
    execution_arn = None

    try:
        arn = os.environ.get('STEPFN_SCHEDULE_SESSION_ARN')
        name = os.environ.get('STEPFN_SCHEDULE_SESSION_NAME')

        response = sfn_client.start_execution(
            stateMachineArn=arn,
            input=json.dumps(input),
            name=f"{name}-{session['Id']}",
            traceHeader='GlobalReview-Schedule-Session'
        )
        execution_arn = response['executionArn']
    except Exception as e:
        cwprint_exc()
        raise e
    
    logs = globalreview.log.log_entry(session['Id'], f"Scheduled Session ({session['Id']}) in destination region {session['Region']}.")

    return execution_arn




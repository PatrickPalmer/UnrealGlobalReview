# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import json
from globalreview.log import log_entry
from globalreview.cwprint import cwprint
import boto3



# Required input:
#   SessionId
#   InstanceId
#   DestinationAmi

def lambda_handler(event, context):

    source_region = os.environ.get('AWS_REGION')
    event['SourceRegion'] = source_region

    destination_region = str(event['DestinationRegion'])

    session_id = event['SessionId']
    instance_id = event['InstanceId']

    ec2_client = boto3.client('ec2', region_name=destination_region)

    try:
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        instance = response['Reservations'][0]['Instances'][0]
    except:
        instance = {}

    if 'PublicIpAddress' not in instance or 'PublicDnsName' not in instance:
       event['PublicState'] = "not_available"
       return event

    log_entry(session_id, f"Launched instance ({instance_id}) Public Ip Address is: {instance['PublicIpAddress']}")
    log_entry(session_id, f"Launched instance ({instance_id}) Public DNS Name is: {instance['PublicDnsName']}")

    dynamodb = boto3.resource('dynamodb')
    session_table_name = json.loads(os.environ.get("DYNAMODB_TABLES"))['session']
    sessions = dynamodb.Table(session_table_name)
    response = sessions.update_item(
        Key={'Id': session_id},
        UpdateExpression='set #PublicIpAddress=:1, #PublicDnsName=:2',
        ExpressionAttributeNames={
            '#PublicIpAddress': 'PublicIpAddress',
            '#PublicDnsName': 'PublicDnsName'
        },
        ExpressionAttributeValues={
            ':1': instance['PublicIpAddress'],
            ':2': instance['PublicDnsName']
        },
        ReturnValues="UPDATED_NEW"
    )
    
    event.update({
        'PublicState': 'available',
        'PublicIpAddress': instance['PublicIpAddress'],
        'PublicDnsName': instance['PublicDnsName'],
    })

    return event

 


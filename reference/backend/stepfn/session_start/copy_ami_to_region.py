# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import json
from datetime import datetime
from globalreview.log import log_entry
import boto3


stage_table_name = json.loads(os.environ.get("DYNAMODB_TABLES"))['stage']


# Required input:
#   SessionId
#   Ami
#   DestinationRegion

def lambda_handler(event, context):
    
    # Source region where the AMI exists
    source_region = os.environ.get('AWS_REGION')
    
    # Destination region where the AMI will be copied
    destination_region = event['DestinationRegion']

    session_id = event['SessionId']
    ami = event['Ami']

    if source_region == destination_region:
        event.update({
            'DestinationAmi': ami,
            'Message': "same region",
        })
        return event

    # Create the EC2 client for the destination region
    destination_ec2_client = boto3.client('ec2', region_name=destination_region)
    
    # check to see if the ami already exists 
    images = destination_ec2_client.describe_images(Filters=[
        {
            'Name': 'tag-key',
            'Values': ['GlobalReview-SourceAmi'],
        },
    ])['Images']

    copied_ami_id = None
    for image in images:
        if 'Tags' in image:
            for t in image['Tags']:
                if t['Key'] == 'GlobalReview-SourceAmi':
                    parts = t['Value'].split(':')
                    if len(parts) == 2:
                        if parts[1] == ami:
                            reason = "ami already existed"
                            copied_ami_id = image['ImageId']
                            log_entry(session_id, f"Session AMI ({copied_ami_id}) already in {destination_region} region.")

    if not copied_ami_id:
        # Copy the AMI to the destination region
        response = destination_ec2_client.copy_image(
            Name='GlobalReview-Copied-AMI',
            SourceRegion=source_region,
            SourceImageId=ami,
            Description=f'Copied {ami} from {source_region} to {destination_region}'
        )
    
        # The response will contain the new AMI ID in the destination region
        copied_ami_id = response['ImageId']
    
        # tag the new AMI 
        destination_ec2_client.create_tags(
            Resources=[copied_ami_id],
            Tags=[
                {
                    'Key': 'GlobalReview-SourceAmi',
                    'Value': f'{source_region}:{ami}'
                },
                {
                    'Key': 'GlobalReview',
                    'Value': 'true'
                },
                {
                    'Key': 'Name',
                    'Value': f'GlobalReview-Copied-{ami}'
                },
            ]
        )

        log_entry(session_id, f"Session AMI ({copied_ami_id}) copied to {destination_region} region.")

        now = datetime.now()
        isonow = now.strftime('%Y-%m-%dT%H:%M:%S%z')

        stage = {
            "Active": True,
            'CreateTime': isonow,
            'UpdateTime': isonow,
            'SourceRegion': os.environ.get('AWS_REGION'),
            'SourceAmi': ami,
            'DestinationRegion': destination_region,
            'Ami': copied_ami_id,
        }
        
        dynamodb = boto3.resource('dynamodb')
        stage_table = dynamodb.Table(stage_table_name)

        stage_table.put_item(Item=stage)

        reason = "ami copied"

    event.update({
        'DestinationAmi': copied_ami_id,
        'Message': reason,
    })

    return event

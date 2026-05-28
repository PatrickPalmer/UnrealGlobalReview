# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from pprint import pprint
from globalreview.log import log_entry
import boto3


# Required input:
#   SessionId
#   Ami
#   DestinationAmi
#   DestinationRegion

def lambda_handler(event, context):
    
    # Destination region where the AMI will be copied
    ami = event['Ami']
    destination_region = event['DestinationRegion']
    destination_ami = event['DestinationAmi']

    session_id = event['SessionId']

    # Create the EC2 client for the destination region
    destination_ec2_client = boto3.client('ec2', region_name=destination_region)
    
    # check to see if the ami already exists 
    images = destination_ec2_client.describe_images(ImageIds=[destination_ami])['Images']
    pprint(images)

    if len(images) == 0:
        msg = f"ERROR: Failed AMI ({ami}) copy to {destination_region} region."
        log_entry(session_id, msg)
        raise IOError(msg)

    state = images[0]['State']

    if state not in ['pending', 'available']:
        msg = f"ERROR: Failed AMI ({ami}) copy to {destination_region} region, state is {state}."
        log_entry(session_id, msg)
        raise IOError(msg)

    event['DestinationAmiState'] = state

    return event

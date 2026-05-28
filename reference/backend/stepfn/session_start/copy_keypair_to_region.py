# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import base64
from globalreview.log import log_entry
import boto3


# Required input:
#   SessionId
#   KeyName
#   DestinationRegion

def lambda_handler(event, context):
    
    # Source region where the keypair exists
    source_region = os.environ.get('AWS_REGION')
    
    # Destination region where the keypair will be copied
    destination_region = str(event['DestinationRegion'])

    session_id = event['SessionId']

    key_name = event['KeyName']
    if not key_name:
        # keypair is optional
        return event

    # Create the EC2 client for the destination region
    destination_ec2_client = boto3.client('ec2', region_name=destination_region)
    
    # check to see if the keypair already exists 
    try:
        keypairs = destination_ec2_client.describe_key_pairs(KeyNames=[key_name])['KeyPairs']
    except:
        keypairs = []

    copied_key_name = False
    if destination_region == source_region:
        copied_key_name = True
    elif keypairs: 
        copied_key_name = True
        log_entry(session_id, f"Key Pair ({key_name}) already in {destination_region} region.")

    if not copied_key_name:
        source_ec2_client = boto3.client('ec2', region_name=source_region)

        try:
            existing_keypairs = source_ec2_client.describe_key_pairs(KeyNames=[key_name], IncludePublicKey=True)['KeyPairs']
        except:
            existing_keypairs = []
            log_entry(session_id, f"ERROR: Unable to find Key Pair ({key_name}) in {source_region} region.")
            event['KeyName'] = None
         
        if existing_keypairs: 
            # make sure the public key is passed in as base64 bytes
            public_key = existing_keypairs[0]['PublicKey']
            if isinstance(public_key, str):
                public_key = base64.b64encode(public_key.encode("utf-8"))

            try:
                response = destination_ec2_client.import_key_pair(KeyName=key_name, PublicKeyMaterial=public_key)
                log_entry(session_id, f"Key Pair ({key_name}) copied to {destination_region} region.")
            except:
                log_entry(session_id, f"ERROR: Unable to copy Key Pair ({key_name}) to {destination_region} region.")
                event['KeyName'] = None

    return event

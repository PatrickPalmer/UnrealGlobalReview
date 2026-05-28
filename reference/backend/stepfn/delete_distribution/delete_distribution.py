# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
from globalreview.log import log_entry
from globalreview.cwprint import cwprint_exc
import boto3


# Required input:
#   SessionId
#   DistributionId
#   DistributionArn
#   DistributionDomainName

def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))

    session_id = event['SessionId'] 
    distribution_id = event["DistributionId"]

    log_entry(session_id, f"Deleting CloudFront Distribution.")

    client = boto3.client('cloudfront')

    distribution = client.get_distribution(Id=distribution_id)
    ETag = distribution['ETag']
    
    client.delete_distribution(Id=distribution_id, IfMatch=ETag) 

    return event


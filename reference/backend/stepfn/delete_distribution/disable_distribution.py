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
    distribution_arn = event["DistributionArn"]
    distribution_domain_name = event["DistributionDomainName"]

    log_entry(session_id, f"Disabling CloudFront Distribution.")

    client = boto3.client('cloudfront')
    distribution=client.get_distribution(Id=distribution_id)

    # first disable the distribution    
    ETag=distribution['ETag']
    distribution_config=distribution['Distribution']['DistributionConfig']
    distribution_config['Enabled']=False
    
    client.update_distribution(DistributionConfig=distribution_config, Id=distribution_id, IfMatch=ETag)

    return event


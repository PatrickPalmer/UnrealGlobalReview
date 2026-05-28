# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import sys
import json
import time
from globalreview.log import log_entry
from globalreview.cwprint import cwprint
import boto3



# Required input:
#   SessionId
#   DistributionId

def lambda_handler(event, context):

    session_id = event['SessionId'] 
    distribution_id = event["DistributionId"]

    client = boto3.client('cloudfront')

    status = client.get_distribution(Id=distribution_id)

    if (status['Distribution']['DistributionConfig']['Enabled'] == False 
        and status['Distribution']['Status'] == 'Deployed'):
        event['DistributionState'] = 'disabled'
    else:
        event['DistributionState'] = 'enabled'

    return event
       

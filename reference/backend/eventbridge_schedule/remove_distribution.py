# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import sys
import json
import copy
import time
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

    log_entry(session_id, f"Starting CloudFront Distribution removal.")

    sfn_client = boto3.client('stepfunctions')

    execution_arn = None

    try:
        arn = os.environ.get('STEPFN_DELETE_DISTRIBUTION_ARN')
        name = os.environ.get('STEPFN_DELETE_DISTRIBUTION_NAME')

        response = sfn_client.start_execution(
            stateMachineArn=arn,
            input=json.dumps(event),
            name=f"{name}-{session_id}",
            traceHeader='GlobalReview-Delete-Distribution'
        )
        execution_arn = response['executionArn']
    except Exception as e:
        cwprint_exc()
        raise e
    
    event['StepFunctionExecutionArn'] = execution_arn

    return event


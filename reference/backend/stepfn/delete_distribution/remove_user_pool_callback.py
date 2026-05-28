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

    # tell cognito app client to remove distribution callback
    user_pool_id = os.environ.get("COGNITO_USER_POOL_ID")
    user_pool_client_id = os.environ.get("COGNITO_USER_POOL_CLIENT_ID")

    cognito_client = boto3.client('cognito-idp')
    try:
        client = cognito_client.describe_user_pool_client(UserPoolId=user_pool_id, ClientId=user_pool_client_id)
    except:
        log_entry(session_id, f"ERROR: Describing and Removing {distribution_domain_name} from User Pool Client ({user_pool_client_id}) failed.")
        cwprint_exc("Cognito Describe User Pool Client")
        return False

    kwargs = client['UserPoolClient']

    domain_url = f"https://{distribution_domain_name}/"
    kwargs['CallbackURLs'] = [c for c in kwargs['CallbackURLs'] if c != domain_url]

    # remove Read Only fields
    del(kwargs['LastModifiedDate'])
    del(kwargs['CreationDate'])
    
    try:
        # update requires you to rewire teh entire contents, not just the changed fields
        resp = cognito_client.update_user_pool_client(**kwargs)
        log_entry(session_id, f"Removing {distribution_domain_name} from User Pool Client ({user_pool_client_id}).")
    except:
        log_entry(session_id, f"ERROR: Removing {distribution_domain_name} from User Pool Client ({user_pool_client_id}) failed.")
        cwprint_exc("Cognito Update User Pool Client")
        return False

    return event


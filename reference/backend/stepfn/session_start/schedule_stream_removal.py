# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import json
import string
import secrets
from globalreview.log import log_entry
from globalreview.cwprint import cwprint, cwprint_exc
import globalreview.terminate
import boto3


# Required input:
#   SessionId
#   InstanceId
#   DestinationRegion
#   EndTime
#   Duration


def get_removal_lambda_function_arn(*, lambda_client=None):
    function_name = 'GlobalReview-Remove-Stream-Copy'

    if lambda_client is None:
        lambda_client = boto3.client('lambda')

    for f in lambda_client.list_functions()['Functions']:
        if f['FunctionName'] == function_name:
            return f['FunctionArn']

    return None


def get_removal_role_arn(*, iam_client=None):
    role_name = 'GlobalReview-Remove-Stream-Copy-Execution-Role'

    if iam_client is None:
        iam_client = boto3.client('iam')

    for r in iam_client.list_roles()['Roles']:
        if r['RoleName'] == role_name:
            return r['Arn']

    return None


def create_scheduled_removal(region, session_id, expired_timestamp, s3_bucket:str, s3_prefix:str, stream:str, *, scheduler_client=None, lambda_client=None, iam_client=None):
    if scheduler_client is None:
        scheduler_client = boto3.client('scheduler')

    # get the lambda target
    target_lambda_arn = get_removal_lambda_function_arn(lambda_client=lambda_client)

    # role arn
    role_arn = get_removal_role_arn(iam_client=iam_client)

    if not target_lambda_arn:
        raise ValueError("Missing GlobalReview Remove Stream Copy lambda_function (GlobalReview-Remove-Stream-Copy)")
    if not role_arn:
        raise ValueError("Missing GlobalReview Remove Stream Copy Role Arn (GlobalReview-Remove-Stream-Copy-Execution-Role)")

    # unique identifier
    alphabet = string.ascii_lowercase + string.digits
    uid = ''.join(secrets.choice(alphabet) for i in range(5))

    name = f'GlobalReview-rmcp-{session_id}-{uid}'

    input = {
        'Operation': 'schedule_stream_removal.create_scheduled_removal',
        'SchedulerClientName': name,
        'Region': region,
        'SessionId': session_id,
        'ExpiredTimestamp': expired_timestamp,
        'S3Bucket': s3_bucket,
        'S3Prefix': s3_prefix, 
        'PerforceStream': stream,
    }

    # check for common scheduler group
    globalreview.terminate.check_scheduler_group_existance(scheduler_client=scheduler_client)

    results = scheduler_client.create_schedule(
        Name=name,
        Description=json.dumps(input),
        GroupName='GlobalReview',
        State='ENABLED',
        ScheduleExpression=f"at({expired_timestamp})",
        FlexibleTimeWindow={ 'Mode': 'OFF' },
        ActionAfterCompletion="DELETE",
        Target={
            'Arn': target_lambda_arn,
            'RoleArn': role_arn,
            'Input': json.dumps(input),
        }
    )

    # add scheduled arn 
    input.update(results)

    return input


def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))

    session_id = event['SessionId']

    end_time = event['EndTime']
    s3_bucket = event['S3Bucket']
    s3_prefix = event['S3Prefix']
    stream = event['PerforceStream']

    region = os.environ.get('AWS_REGION')

    # developer testing
    if 'SkipP4S3Copy' in event:
        return event

    # scheduler doesn't work with UTC notation
    if end_time.endswith('Z'):
        end_time = end_time[:-1]    

    try:
        r = create_scheduled_removal(region, session_id, end_time, s3_bucket, s3_prefix, stream)
        cwprint(r, header="Create Scheduled Stream Removal")
    except Exception as e:
        log_entry(session_id, f"ERROR: Scheduled Stream Copy removal failed.")
        log_entry(session_id, f"ERROR: Reason: {e}")
        msg = cwprint_exc("ERROR: Scheduled Removal")
        log_entry(session_id, msg)
        raise

    log_entry(session_id, f"Scheduled S3 Removal.")

    return event



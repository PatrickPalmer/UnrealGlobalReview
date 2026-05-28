# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""

Links:
   https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/scheduler.html

"""

import json
import string
import secrets
from datetime import datetime
from .log import log_entry
from .cwprint import cwprint_exc
import boto3


def create_alphanumeric_random_string(length=10):
    alphabet = string.ascii_lowercase + string.digits
    access_token = ''.join(secrets.choice(alphabet) for i in range(length))
    return access_token


def get_scheduler_group_arn(*, scheduler_client=None):
    if scheduler_client is None:
        scheduler_client = boto3.client('scheduler')

    groups = scheduler_client.list_schedule_groups()

    arn = None
    try:
        for g in groups['ScheduleGroups']:
            if g['Name'] == 'GlobalReview':
                arn = g['Arn']
    except:
        arn = None

    if not arn:
        results = scheduler_client.create_schedule_group(Name='GlobalReview')
        arn = results['ScheduleGroupArn']

    return arn


def check_scheduler_group_existance(*, scheduler_client=None):
    return get_scheduler_group_arn(scheduler_client=scheduler_client) is not None


def get_terminate_lambda_function_arn(*, lambda_client=None):
    function_name = 'GlobalReview-Terminate-Instance'

    if lambda_client is None:
        lambda_client = boto3.client('lambda')

    for f in lambda_client.list_functions()['Functions']:
        if f['FunctionName'] == function_name:
            return f['FunctionArn']

    return None


def get_terminate_role_arn(*, iam_client=None):
    role_name = 'GlobalReview-Terminate-Instance-Execution-Role'

    if iam_client is None:
        iam_client = boto3.client('iam')

    for r in iam_client.list_roles()['Roles']:
        if r['RoleName'] == role_name:
            return r['Arn']

    return None
    

def delete_scheduled_termination(region, instance_id, session_id, *, scheduler_client=None):
    if scheduler_client is None:
        scheduler_client = boto3.client('scheduler')

    deleted = []

    schedules = scheduler_client.list_schedules(GroupName='GlobalReview')
    for schedule in schedules['Schedules']:
        parts = schedule['Name'].split('-', 3)
        if len(parts) == 4 and parts[0] == 'GlobalReview' and parts[1] == instance_id:
            response = scheduler_client.get_schedule(GroupName='GlobalReview', Name=schedule['Name'])
            if not response or 'Name' not in response:
                continue
            scheduler_client.delete_schedule(GroupName='GlobalReview', Name=schedule['Name'])
            deleted.append(schedule['Name'])

    return deleted                  


def create_scheduled_termination(
    region, 
    instance_id, 
    session_id, 
    expired_timestamp, 
    *, 
    scheduler_client=None, 
    lambda_client=None, 
    iam_client=None, 
    **kwargs
):
    if scheduler_client is None:
        scheduler_client = boto3.client('scheduler')

    # get the lambda target
    target_lambda_arn = get_terminate_lambda_function_arn(lambda_client=lambda_client)
    if not target_lambda_arn:
        raise ValueError("Missing GlobalReview Terminate lambda_function")

    # role arn
    role_arn = get_terminate_role_arn(iam_client=iam_client)
    if not role_arn:
        raise ValueError("Missing GlobalReview Terminate Role Arn")

    # delete any existing scheduled denys
    delete_scheduled_termination(region, instance_id, session_id, scheduler_client=scheduler_client)

    uid = create_alphanumeric_random_string(10)
    name = f'GlobalReview-{instance_id}-{uid}-{region}'

    input = {
        'Operation': 'terminate.create_scheduled_termination',
        'SchedulerClientName': name,
        'Region': region,
        'InstanceId': instance_id,
        'SessionId': session_id,
        'ExpiredTimestamp': expired_timestamp,
    } | kwargs

    # check for common scheduler group
    check_scheduler_group_existance(scheduler_client=scheduler_client)

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

    input.update(results)
    
    return input


def get_scheduled_termination(region, *, instance_id=None, session_id=None, filter_user_arn=None, scheduler_client=None
):
    """
    Returns: list of pairs (user_role_arn, expired_date)
    """
    if scheduler_client is None:
        scheduler_client = boto3.client('scheduler')

    scheduled = []

    schedules = scheduler_client.list_schedules(GroupName='GlobalReview')
    for schedule in schedules['Schedules']:
        parts = schedule['Name'].split('-', 3)
        if len(parts) == 5 and parts[0] == 'GlobalReview' and parts[1] == instance_id:
            response = scheduler_client.get_schedule(GroupName='GlobalReview', Name=schedule['Name'])
            if not response or 'Name' not in response:
                continue
            try:
                desc = json.loads(response['Description'])
            except ValueError:
                # it should be valid json, 
                continue

            add = False
            if instance_id and desc['instance_id'] == instance_id:
                add = True
            if session_id and desc['session_id'] == session_id:
                add = True

            if add:
                scheduled.append(desc)

    return scheduled


def terminate_instance(region, *, instance_id=None, session_id=None, ec2_client=None, verbose=True) -> bool:

    if not ec2_client:
        ec2_client = boto3.client('ec2', region_name=region)

    # check to see if the instance has already been terminated
    try:
        response = ec2_client.describe_instances(InstanceIds=[ instance_id ])
        instances = response['Reservations'][0]['Instances']
    except Exception as e:
        cwprint_exc("Describing Instances for Termination")
        if verbose:
            log_entry(session_id, f"Warning: Instance ({instance_id}) not available ({region}).")
        raise

    if len(instances) == 0:
        if verbose:
            log_entry(session_id, f"Termination: Instance ({instance_id}) in region {region} not running.")
        return False
    if instances[0]['State']['Name'] not in ['pending', 'running']:
        if verbose:
            log_entry(session_id, f"Termination: Instance ({instance_id}) in region {region} not running (state {instances[0]['State']['Name']}).")
        return False

    # Terminate instance
    try:
        response = ec2_client.terminate_instances(InstanceIds=[ instance_id ])
    except Exception as e:
        msg = cwprint_exc("ERROR: Termination")
        if verbose:
            log_entry(session_id, f"ERROR: Termination failed.")
            log_entry(session_id, msg)
        raise

    if verbose:
        log_entry(session_id, f"Termination started.")

    return True

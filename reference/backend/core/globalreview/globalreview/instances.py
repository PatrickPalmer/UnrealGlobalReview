# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import sys
import boto3


def get_instances_running_in_region(region_name:str, only_global_review_tagged:bool=True):
    ec2_client = boto3.client('ec2', region_name=region_name)

    if only_global_review_tagged:
        response = ec2_client.describe_instances(Filters=[{
            'Name': 'tag-key',
            'Values': ['GlobalReview',]
        }])
    else:
        response = ec2_client.describe_instances()

    instances = []
    if 'Reservations' in response and len(response['Reservations']):
        for reservation in response['Reservations']:
            if 'Instances' in reservation:
                for instance in reservation['Instances']:
                    instances.append(instance)

    return instances


def get_instances_running_in_region_as_dict(region_name:str, only_global_review_tagged:bool=True):
    results = []
    instances = get_instances_running_in_region(region_name, only_global_review_tagged)

    for instance in instances:

        is_global_review = False
        if 'Tags' in instance:
            for tag in instance['Tags']:
                if 'Key' in tag and tag['Key'] == 'GlobalReview':
                    is_global_review = True
        instance["GlobalReview"] = is_global_review

        results.append(instance)

    return results


def get_instance_types(region_name:str):
    '''Yield all available EC2 instance types in region <region_name>'''
    ec2 = boto3.client('ec2', region_name=region_name)
    describe_args = {}
    while True:
        describe_result = ec2.describe_instance_types(**describe_args)
        yield from [i['InstanceType'] for i in describe_result['InstanceTypes']]
        if 'NextToken' not in describe_result:
            break
        describe_args['NextToken'] = describe_result['NextToken']


def has_instance_type(instance_type:str, region_name:str) -> bool:
    ec2 = boto3.client('ec2', region_name=region_name)
    describe_result = ec2.describe_instance_types(InstanceTypes=[instance_type])
    return len(describe_result['InstanceTypes']) > 0
    
    
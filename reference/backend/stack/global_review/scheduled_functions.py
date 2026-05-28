# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import json

from constructs import Construct
from aws_cdk import (
    Duration,
    aws_iam as iam,
    aws_lambda,
    Tags,
)
import cdk_nag as nag

SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


def create_terminate_instance_function(stack, core_lambda_layer, review_lambda_layer, log_group):

    # scheduler terminate role
    exec_role = iam.Role(stack, 'GlobalReview-Terminate-Instance-Execution-Role', 
        role_name='GlobalReview-Terminate-Instance-Execution-Role', 
        assumed_by=iam.ServicePrincipal('scheduler.amazonaws.com'),
    )
    exec_role.add_to_policy(iam.PolicyStatement(
      actions=["lambda:InvokeFunction",],
      resources=[f"arn:{stack.partition}:lambda:{stack.region}:{stack.account}:function:GlobalReview-Terminate-Instance",]
    ))

    # terminate lambda role
    lambda_role = iam.Role(stack, 'GlobalReview-Terminate-Instance-Role', 
        assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
    )
    lambda_role.add_to_policy(iam.PolicyStatement(
      actions=["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
      resources=[f"arn:{stack.partition}:logs:*:*:*"],
    ))
    lambda_role.add_to_policy(iam.PolicyStatement(
      actions=["ec2:DescribeInstances",
               "ec2:TerminateInstances"],
      resources=["*"],
    ))
    lambda_role.add_to_policy(iam.PolicyStatement(
      actions=["cognito-idp:DescribeUserPoolClient",
               "cognito-idp:UpdateUserPoolClient"],
      resources=["*"],
    ))

    nag.NagSuppressions.add_resource_suppressions(
        lambda_role,
        [
            {
                'id': "AwsSolutions-IAM5",
                'reason': "Lambda should be able to log",
                'applies_to': [ "Resource::*" ]
            },
        ], True
    )

    with open(os.path.join(SCRIPT_DIRECTORY, '..', '..', "eventbridge_schedule", "terminate-instance.py")) as fd:
        code = fd.read()

    terminate_fn = aws_lambda.Function(
        stack,
        id='GlobalReview-Terminate-Instance',
        function_name='GlobalReview-Terminate-Instance',
        runtime=aws_lambda.Runtime.PYTHON_3_13,
        handler='index.lambda_handler',
        role=lambda_role,
        code=aws_lambda.Code.from_inline(code),
        timeout=Duration.seconds(60),
        layers=[core_lambda_layer, review_lambda_layer],
        environment = {
            "AWS_PARTITION": stack.partition,
            "LOG_GROUP_NAME": log_group.log_group_name,
        },
        retry_attempts=0,
        memory_size=256, # MB
    )

    return terminate_fn, lambda_role, exec_role


def create_remove_distribution_function(
    stack, 
    core_lambda_layer, 
    review_lambda_layer, 
    log_group,
    user_pool, 
    user_client, 
    cognito_domain,
    delete_dist_stepfn,
):

    # scheduler remove distribution role
    exec_role = iam.Role(stack, 'GlobalReview-Remove-Distribution-Execution-Role', 
        role_name='GlobalReview-Remove-Distribution-Execution-Role', 
        assumed_by=iam.ServicePrincipal('scheduler.amazonaws.com'),
    )
    exec_role.add_to_policy(iam.PolicyStatement(
      actions=["lambda:InvokeFunction",],
      resources=[f"arn:{stack.partition}:lambda:{stack.region}:{stack.account}:function:GlobalReview-Remove-Distribution"]
    ))

    # remove distribution lambda role
    lambda_role = iam.Role(stack, 'GlobalReview-Remove-Distribution-Role', 
        assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
    )
    lambda_role.add_to_policy(iam.PolicyStatement(
      actions=["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
      resources=[f"arn:{stack.partition}:logs:*:{stack.account}:*"],
    ))
    lambda_role.add_to_policy(iam.PolicyStatement(
      actions=["cloudfront:DeleteDistribution",
               "cloudfront:GetDistribution",
               "cloudfront:UpdateDistribution",],
      resources=["*"],
    ))
    lambda_role.add_to_policy(iam.PolicyStatement(
      actions=["cognito-idp:DescribeUserPoolClient",
               "cognito-idp:UpdateUserPoolClient"],
      resources=["*"],
    ))
    lambda_role.add_to_policy(iam.PolicyStatement(
      actions=["states:StartExecution"],
      resources=[delete_dist_stepfn.state_machine_arn]
    ))
    lambda_role.add_to_policy(iam.PolicyStatement(
      actions=["states:DescribeExecution"],
      resources=['*']
    ))

    nag.NagSuppressions.add_resource_suppressions(
        lambda_role,
        [
            {
                'id': "AwsSolutions-IAM5",
                'reason': ','.join(["Lambda should be able to log", 
                           "able to delete created cloudfront distributions",
                           "retrieve info about user pool",
                           "retrieve info about step function execution"]),
                'applies_to': [ "Resource::*" ]
            },
        ], True
    )

    with open(os.path.join(SCRIPT_DIRECTORY, '..', '..', "eventbridge_schedule", "remove_distribution.py")) as fd:
        code = fd.read()

    fn = aws_lambda.Function(
        stack,
        id='GlobalReview-Remove-Distribution',
        function_name='GlobalReview-Remove-Distribution',
        runtime=aws_lambda.Runtime.PYTHON_3_13,
        handler='index.lambda_handler',
        role=lambda_role,
        code=aws_lambda.Code.from_inline(code),
        timeout=Duration.seconds(800),
        layers=[core_lambda_layer, review_lambda_layer],
        environment = {
            "AWS_PARTITION": stack.partition,
            "LOG_GROUP_NAME": log_group.log_group_name,
            "USER_POOL_ID": user_pool.user_pool_id,
            "USER_POOL_APP_ID": user_client.user_pool_client_id,
            "USER_POOL_DOMAIN_NAME": cognito_domain.domain_name,
            "STEPFN_DELETE_DISTRIBUTION_ARN": delete_dist_stepfn.state_machine_arn,
            "STEPFN_DELETE_DISTRIBUTION_NAME": delete_dist_stepfn.state_machine_name,
        },
        retry_attempts=0,
        memory_size=256, # MB
    )

    return fn, lambda_role, exec_role


def create_remove_stream_copy_function(
    stack, 
    core_lambda_layer, 
    review_lambda_layer, 
    log_group
):

    # scheduler role
    exec_role = iam.Role(stack, 'GlobalReview-Remove-Stream-Copy-Execution-Role', 
        role_name='GlobalReview-Remove-Stream-Copy-Execution-Role', 
        assumed_by=iam.ServicePrincipal('scheduler.amazonaws.com'),
    )
    exec_role.add_to_policy(iam.PolicyStatement(
      actions=["lambda:InvokeFunction",],
      resources=[f"arn:{stack.partition}:lambda:{stack.region}:{stack.account}:function:GlobalReview-Remove-Stream-Copy"],
    ))

    # lambda role
    lambda_role = iam.Role(stack, 'GlobalReview-Remove-Stream-Copy-Role', 
        assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
    )
    lambda_role.add_to_policy(iam.PolicyStatement(
      actions=["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
      resources=[f"arn:{stack.partition}:logs::{stack.account}:*"],
    ))
    lambda_role.add_to_policy(iam.PolicyStatement(
      actions=["s3:DeleteObject",
               "s3:ListBucket",],
      resources=[f"arn:{stack.partition}:s3:::*"],
    ))

    nag.NagSuppressions.add_resource_suppressions(
        lambda_role,
        [
            {
                'id': "AwsSolutions-IAM5",
                'reason': ','.join(["Lambda should be able to log", 
                           "delete temp copy of Perforce Helix Stream"]),
                'applies_to': [ "Resource::*" ]
            },
        ], True
    )

    with open(os.path.join(SCRIPT_DIRECTORY, '..', '..', "eventbridge_schedule", "rm_stream_copy.py")) as fd:
        code = fd.read()

    removal_fn = aws_lambda.Function(
        stack,
        id='GlobalReview-Remove-Stream-Copy',
        function_name='GlobalReview-Remove-Stream-Copy',
        runtime=aws_lambda.Runtime.PYTHON_3_13,
        handler='index.lambda_handler',
        role=lambda_role,
        code=aws_lambda.Code.from_inline(code),
        timeout=Duration.seconds(60),
        layers=[core_lambda_layer, review_lambda_layer],
        environment = {
            "LOG_GROUP_NAME": log_group.log_group_name,
        },
        retry_attempts=0,
        memory_size=256, # MB
    )

    return removal_fn, lambda_role, exec_role


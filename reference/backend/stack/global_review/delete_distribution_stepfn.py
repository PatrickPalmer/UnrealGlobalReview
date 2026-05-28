# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os

from aws_cdk import (
    Duration,
    aws_iam as iam,
    aws_lambda,
    aws_stepfunctions as stepfn,
    aws_stepfunctions_tasks as stepfn_tasks,
)
import cdk_nag as nag

SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


def create_delete_distribution_step_function(
    stack, 
    lambda_layers, 
    log_group,
    user_pool,
    user_client
):

    # step function role
    lambda_role = iam.Role(stack, 'GlobalReview-Delete-Distribution-Role', 
        assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
    )
    lambda_role.add_to_policy(iam.PolicyStatement(
        actions=["logs:CreateLogGroup", "logs:CreateLogStream", 
                 "logs:FilterLogEvents", "logs:PutLogEvents"],
        resources=[f"arn:{stack.partition}:logs:*:*:*"],
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

    nag.NagSuppressions.add_resource_suppressions(
        lambda_role,
        [
            {
                'id': "AwsSolutions-IAM5",
                'reason': ','.join(["Lambda should be able to log", 
                           "descrive / delete a cloudfront distribution",
                           "update user pool w cloudfront distribution",]),
                'applies_to': [ "Resource::*" ]
            },
        ], True
    )

    environment = {
        "COGNITO_USER_POOL_REGION": stack.cognito_auth_region,
        "COGNITO_USER_POOL_ID": user_pool.user_pool_id,
        "COGNITO_USER_POOL_CLIENT_ID": user_client.user_pool_client_id,
        "LOG_GROUP_NAME": log_group.log_group_name,
    }

    # Step 1: remove user pool callback
    rmcb_job = _remove_user_pool_callback_task(stack, lambda_layers, lambda_role, environment)

    # Step 2: disable distribution
    disable_job = _disable_distribution_task(stack, lambda_layers, lambda_role, environment)

    # Step 3: wait for distribution to be disabled (not instant)
    is_disabled_job = _create_is_dist_disabled_task(stack, lambda_layers, lambda_role, environment)
    disabled_wait_job = stepfn.Wait(
        stack, "GlobalReview-Disable-Distribution-Wait",
        time=stepfn.WaitTime.duration(Duration.seconds(120))
    )

    # Step 4: delete distribution
    delete_job = _delete_distribution_task(stack, lambda_layers, lambda_role, environment)

    # Step Function definition
    chain = (rmcb_job
             .next(disable_job)
             .next(disabled_wait_job)
             .next(is_disabled_job)
             .next(stepfn.Choice(stack, 'GlobalReview-Is-Disabled-Complete?')
                 .when(stepfn.Condition.string_equals('$.DistributionState', 'disabled'), 
                       delete_job)
                 .otherwise(disabled_wait_job)
                 .afterwards())
            )

    # Create State Machine
    sm = stepfn.StateMachine(stack, 'GlobalReview-Delete-Distribution-StepFn', 
        state_machine_name='GlobalReview-Delete-Distribution-StepFn', 
        definition_body=stepfn.DefinitionBody.from_chainable(chain),
        logs=stepfn.LogOptions(
            destination=log_group,
            level=stepfn.LogLevel.ALL
        ),
        tracing_enabled=True
    )

    nag.NagSuppressions.add_resource_suppressions(
        sm,
        [
            {
                'id': "AwsSolutions-IAM5",
                'reason': "Access to functions", 
                'applies_to': [ "Resource::*" ]
            },
        ], True
    )

    return sm, lambda_role


def _remove_user_pool_callback_task(stack, lambda_layers, lambda_role, environment):
    with open(os.path.join(SCRIPT_DIRECTORY, '..', '..', "stepfn", "delete_distribution", "remove_user_pool_callback.py")) as fd:
        code = fd.read()

    rm_fn = aws_lambda.Function(
        stack,
        id='GlobalReview-Remove-UserPool-Callback',
        function_name='GlobalReview-Remove-UserPool-Callback', 
        runtime=aws_lambda.Runtime.PYTHON_3_13,
        handler='index.lambda_handler',
        role=lambda_role,
        code=aws_lambda.Code.from_inline(code),
        timeout=Duration.seconds(60),
        layers=lambda_layers,
        environment=environment,
        retry_attempts=0,
        memory_size=256, # MB
    )

    rm_job = stepfn_tasks.LambdaInvoke(stack, "GlobalReview-Remove-UserPool-Callback-Task",
        lambda_function=rm_fn,
        output_path="$.Payload",
    )

    return rm_job


def _disable_distribution_task(stack, lambda_layers, lambda_role, environment):
    with open(os.path.join(SCRIPT_DIRECTORY, '..', '..', "stepfn", "delete_distribution", "disable_distribution.py")) as fd:
        code = fd.read()

    fn = aws_lambda.Function(
        stack,
        id='GlobalReview-Disable-Distribution',
        function_name='GlobalReview-Disable-Distribution', 
        runtime=aws_lambda.Runtime.PYTHON_3_13,
        handler='index.lambda_handler',
        role=lambda_role,
        code=aws_lambda.Code.from_inline(code),
        timeout=Duration.seconds(60),
        layers=lambda_layers,
        environment=environment,
        retry_attempts=0,
        memory_size=256, # MB
    )

    job = stepfn_tasks.LambdaInvoke(stack, "GlobalReview-Disable-Distribution-Task",
        lambda_function=fn,
        output_path="$.Payload",
    )

    return job


def _create_is_dist_disabled_task(stack, lambda_layers, lambda_role, environment):
    with open(os.path.join(SCRIPT_DIRECTORY, '..', '..', "stepfn", "delete_distribution", "is_dist_disabled.py")) as fd:
        code = fd.read()

    fn = aws_lambda.Function(
        stack,
        id='GlobalReview-Is-Distribution-Disabled',
        function_name='GlobalReview-Is-Distribution-Disabled', 
        runtime=aws_lambda.Runtime.PYTHON_3_13,
        handler='index.lambda_handler',
        role=lambda_role,
        code=aws_lambda.Code.from_inline(code),
        timeout=Duration.seconds(60),
        layers=lambda_layers,
        environment=environment,
        retry_attempts=0,
        memory_size=256, # MB
    )

    job = stepfn_tasks.LambdaInvoke(stack, "GlobalReview-Is-Distribution-Disabled-Task",
        lambda_function=fn,
        output_path="$.Payload",
    )

    return job


def _delete_distribution_task(stack, lambda_layers, lambda_role, environment):
    with open(os.path.join(SCRIPT_DIRECTORY, '..', '..', "stepfn", "delete_distribution", "delete_distribution.py")) as fd:
        code = fd.read()

    fn = aws_lambda.Function(
        stack,
        id='GlobalReview-Delete-Distribution',
        function_name='GlobalReview-Delete-Distribution', 
        runtime=aws_lambda.Runtime.PYTHON_3_13,
        handler='index.lambda_handler',
        role=lambda_role,
        code=aws_lambda.Code.from_inline(code),
        timeout=Duration.seconds(60),
        layers=lambda_layers,
        environment=environment,
        retry_attempts=0,
        memory_size=256, # MB
    )

    job = stepfn_tasks.LambdaInvoke(stack, "GlobalReview-Delete-Distribution-Task",
        lambda_function=fn,
        output_path="$.Payload",
    )

    return job


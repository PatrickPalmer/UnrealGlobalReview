# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os

from aws_cdk import (
    Duration,
    aws_iam as iam,
    aws_lambda,
    aws_stepfunctions as stepfn,
    aws_stepfunctions_tasks as stepfn_tasks,
    Size,
)
import cdk_nag as nag

from .cdk_lambda_layer_builder.constructs import BuildPyLayerAsset

SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


def create_s3cmd_layer(stack) -> aws_lambda.LayerVersion:

    # create the pipy layer
    layer_asset = BuildPyLayerAsset.from_pypi(stack, 'GlobalReview-S3Cmd-Layer-Asset',
        pypi_requirements=[
            's3cmd', 
        ],
        py_runtime=aws_lambda.Runtime.PYTHON_3_13,
    )
    layer = aws_lambda.LayerVersion(
        stack,
        id='GlobalReview-S3Cmd-Layer',
        layer_version_name='GlobalReview-S3Cmd-Layer',
        code=aws_lambda.Code.from_bucket(layer_asset.asset_bucket, layer_asset.asset_key),
        compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_13],
        description ='S3Cmd'
    )
    return layer


def create_schedule_session_step_function(stack, 
    lambda_layers, 
    content_bucket, 
    tables, 
    tables_json, 
    log_group,
    session_role,
    instance_profile,
    user_pool,
    user_client,
    cognito_domain,
):

    # step function role
    lambda_role = iam.Role(stack, 'GlobalReview-Start-Session-Role', 
        assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
    )
    lambda_role.add_to_policy(iam.PolicyStatement(
        actions=["logs:CreateLogGroup", "logs:CreateLogStream", 
                 "logs:FilterLogEvents", "logs:PutLogEvents"],
        resources=[f"arn:{stack.partition}:logs:*:{stack.account}:*"],
    ))
    lambda_role.add_to_policy(iam.PolicyStatement(
        actions=["s3:DeleteObject",
                 "s3:ListBucket",
                 "s3:GetObject",
                 "s3:GetBucketLocation",
                 "s3:PutObject", ],
        resources= [content_bucket.bucket_arn,
                    content_bucket.bucket_arn + "/*"]
    ))
    lambda_role.add_to_policy(iam.PolicyStatement(
        actions=["ec2:AuthorizeSecurityGroupIngress", 
                 "ec2:CopyImage",
                 "ec2:CreateSecurityGroup",
                 "ec2:CreateTags",
                 "ec2:DescribeImages",
                 "ec2:DescribeInstances",
                 "ec2:DescribeInstanceTypes",
                 "ec2:DescribeInstanceTypeOfferings",
                 "ec2:DescribeKeyPairs",
                 "ec2:DescribeManagedPrefixLists",
                 "ec2:DescribeSecurityGroups",
                 "ec2:DescribeSubnets",
                 "ec2:DescribeVpcs", 
                 "ec2:ImportKeyPair",
                 "ec2:RunInstances", 
                 "ec2:TerminateInstances"],
        resources=["*"],
    ))
    lambda_role.add_to_policy(iam.PolicyStatement(
      actions=["dynamodb:PutItem",
               "dynamodb:UpdateItem"],
      resources= [t.table_arn for t in tables],
    ))
    lambda_role.add_to_policy(iam.PolicyStatement(
      actions=["iam:ListRoles", "iam:ListInstanceProfiles", "iam:PassRole"],
      resources=["*"],
    ))
    lambda_role.add_to_policy(iam.PolicyStatement(
      actions=["lambda:EnableReplication",
               "lambda:GetFunction",
               "lambda:ListFunctions"],
      resources=["*"],
    ))
    lambda_role.add_to_policy(iam.PolicyStatement(
      actions=["scheduler:ListScheduleGroups", 
               "scheduler:CreateScheduleGroup",
               "scheduler:CreateSchedule",
               "scheduler:ListSchedules"],
      resources=["*"],
    ))
    lambda_role.add_to_policy(iam.PolicyStatement(
      actions=["ssm:DeleteParameter",
               "ssm:GetParameter"],
      resources=["*"],
    ))
    lambda_role.add_to_policy(iam.PolicyStatement(
      actions=["cloudfront:CreateDistribution",],
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
                           "ec2 / network info gather and create",
                           "able to list lambda functions",
                           "start and describe step functions",
                           "read/write to dynamodb tables",
                           "schedule tasks",
                           "read/write to the SSM Parameter store",
                           "create a cloudfront distribution",
                           "update user pool w cloudfront distribution",]),
                'applies_to': [ "Resource::*" ]
            },
        ], True
    )

    environment = {
        "AWS_PARTITION": stack.partition,
        "COGNITO_USER_POOL_REGION": stack.cognito_auth_region,
        "COGNITO_USER_POOL_ID": user_pool.user_pool_id,
        "COGNITO_USER_POOL_CLIENT_ID": user_client.user_pool_client_id,
        "COGNITO_USER_POOL_CLOUDFRONT_DOMAIN": cognito_domain.cloud_front_domain_name,
        "DYNAMODB_TABLES": tables_json,
        "AWS_DEPLOYMENT_REGION": stack.region,
        "LOG_GROUP_NAME": log_group.log_group_name,
        "CONTENT_BUCKET_ARN": content_bucket.bucket_arn,
        "CONTENT_BUCKET_NAME": content_bucket.bucket_name,
        "INSTANCE_PROFILE_ARN": instance_profile.attr_arn,
        "SESSION_ROLE_ARN": session_role.role_arn,
        "SESSION_ROLE_NAME": session_role.role_name,
    }

    # Step 1: ready network infrastructure
    network_job = _create_network_task(stack, lambda_layers, lambda_role, environment)

    # Step 2: copy keypair to region
    copy_keypair_job = _create_copy_keypair_task(stack, lambda_layers, lambda_role, environment)

    # Step 3: copy ami to region
    copy_ami_job = _create_copy_ami_task(stack, lambda_layers, lambda_role, environment)

    # Step 3A: wait for ami to be copied (not instant)
    is_copied_job = _create_is_ami_copied_task(stack, lambda_layers, lambda_role, environment)
    ami_wait_job = stepfn.Wait(
        stack, "GlobalReview-Copy-AMI-Wait",
        time=stepfn.WaitTime.duration(Duration.seconds(30))
    )

    # Step 4: Copy Perforce data to S3
    p4s3_job = _create_p4s3xfer_task(stack, lambda_layers, lambda_role, environment)

    # Step 5: Start Session Task
    start_session_job = _create_start_session_task(stack, lambda_layers, lambda_role, environment)

    # Step 5A: Wait for Public IP Address and DNS Name
    is_session_public_job = _create_is_session_public_task(stack, lambda_layers, lambda_role, environment)
    public_wait_job = stepfn.Wait(
        stack, "GlobalReview-Session-Public-Wait",
        time=stepfn.WaitTime.duration(Duration.seconds(15))
    )

    # Step 6: Schedule termination
    terminate_job = _create_schedule_termination_task(stack, lambda_layers, lambda_role, environment)

    # Step 7: Schedule Remove Perforce copy
    rmcp_job = _create_schedule_remove_stream_copy_task(stack, lambda_layers, lambda_role, environment)

    # Step 8: Create CloudFront Distribution
    dist_job = _create_distribution_task(stack, lambda_layers, lambda_role, environment)
  
    # Step 8: Schedule CloudFront Distribution
    rmcf_job = _create_schedule_remove_distribution_task(stack, lambda_layers, lambda_role, environment)

    # Step Function definition
    chain = (network_job
            .next(copy_keypair_job)
            .next(copy_ami_job)
            .next(ami_wait_job)
            .next(is_copied_job)
            .next(stepfn.Choice(stack, 'GlobalReview-Is-Copy-Complete?')
                .when(stepfn.Condition.string_equals('$.DestinationAmiState', 'available'), 
                    p4s3_job
                    .next(rmcp_job)
                    .next(start_session_job)
                    .next(terminate_job)
                    .next(public_wait_job)
                    .next(is_session_public_job)
                    .next(stepfn.Choice(stack, 'GlobalReview-Is-Public-Complete?')
                    .when(stepfn.Condition.string_equals('$.PublicState', 'available'), 
                        dist_job
                            .next(rmcf_job))
                        .otherwise(public_wait_job)
                        .afterwards())
              )
              .otherwise(ami_wait_job)
              .afterwards())
          )

    # Create State Machine
    sm = stepfn.StateMachine(stack, 'GlobalReview-Schedule-Session-StepFn', 
        state_machine_name='GlobalReview-Schedule-Session-StepFn', 
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


def _create_network_task(stack, lambda_layers, lambda_role, environment):
    with open(os.path.join(SCRIPT_DIRECTORY, '..', '..', "stepfn", "session_start", "check_network.py")) as fd:
        code = fd.read()

    network_fn = aws_lambda.Function(
        stack,
        id='GlobalReview-Check-Region-Network',
        function_name='GlobalReview-Check-Region-Network', 
        runtime=aws_lambda.Runtime.PYTHON_3_13,
        handler='index.lambda_handler',
        role=lambda_role,
        code=aws_lambda.Code.from_inline(code),
        timeout=Duration.seconds(60),
        layers=lambda_layers,
        environment=environment,
        retry_attempts=0,
        memory_size=128, # 128MB
    )

    network_job = stepfn_tasks.LambdaInvoke(stack, "GlobalReview-Check-Region-Network-Task",
        lambda_function=network_fn,
        output_path="$.Payload",
    )

    return network_job


def _create_copy_keypair_task(stack, lambda_layers, lambda_role, environment):
    with open(os.path.join(SCRIPT_DIRECTORY, '..', '..', "stepfn", "session_start", "copy_keypair_to_region.py")) as fd:
        code = fd.read()

    copy_fn = aws_lambda.Function(
        stack,
        id='GlobalReview-Copy-Keypair-To-Region',
        function_name='GlobalReview-Copy-Keypair-To-Region', 
        runtime=aws_lambda.Runtime.PYTHON_3_13,
        handler='index.lambda_handler',
        role=lambda_role,
        code=aws_lambda.Code.from_inline(code),
        timeout=Duration.seconds(600),
        layers=lambda_layers,
        environment=environment,
        retry_attempts=0,
        memory_size=256, # MB
    )

    copy_job = stepfn_tasks.LambdaInvoke(stack, "GlobalReview-Copy-Keypair-To-Region-Task",
        lambda_function=copy_fn,
        output_path="$.Payload",
    )

    return copy_job


def _create_copy_ami_task(stack, lambda_layers, lambda_role, environment):
    with open(os.path.join(SCRIPT_DIRECTORY, '..', '..', "stepfn", "session_start", "copy_ami_to_region.py")) as fd:
        code = fd.read()

    copy_fn = aws_lambda.Function(
        stack,
        id='GlobalReview-Copy-Ami-To-Region',
        function_name='GlobalReview-Copy-Ami-To-Region', 
        runtime=aws_lambda.Runtime.PYTHON_3_13,
        handler='index.lambda_handler',
        role=lambda_role,
        code=aws_lambda.Code.from_inline(code),
        timeout=Duration.seconds(600),
        layers=lambda_layers,
        environment=environment,
        retry_attempts=0,
        memory_size=256, # MB
    )

    copy_job = stepfn_tasks.LambdaInvoke(stack, "GlobalReview-Copy-Ami-To-Region-Task",
        lambda_function=copy_fn,
        output_path="$.Payload",
    )

    return copy_job


def _create_is_ami_copied_task(stack, lambda_layers, lambda_role, environment):
    with open(os.path.join(SCRIPT_DIRECTORY, '..', '..', "stepfn", "session_start", "is_ami_copied.py")) as fd:
        code = fd.read()

    copied_fn = aws_lambda.Function(
        stack,
        id='GlobalReview-Is-Ami-Copied',
        function_name='GlobalReview-Is-AmiCopied', 
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

    copied_job = stepfn_tasks.LambdaInvoke(stack, "GlobalReview-Is-Ami-Copied-Task",
        lambda_function=copied_fn,
        output_path="$.Payload",
    )

    return copied_job


def _create_p4s3xfer_task(stack, lambda_layers, lambda_role, environment):
    with open(os.path.join(SCRIPT_DIRECTORY, '..', '..', "stepfn", "session_start", "p4s3xfer.py")) as fd:
        code = fd.read()

    # @FUTURE: make an option
    #s3cmd_layer = [stack.create_s3cmd_layer()]
    s3cmd_layer = []

    p4s3_fn = aws_lambda.Function(
        stack,
        id='GlobalReview-PerforceHelix-To-S3',
        function_name='GlobalReview-PerforceHelix-To-S3',
        runtime=aws_lambda.Runtime.PYTHON_3_13,
        handler='index.lambda_handler',
        role=lambda_role,
        code=aws_lambda.Code.from_inline(code),
        timeout=Duration.seconds(900),
        layers=lambda_layers + s3cmd_layer,
        environment=environment,
        retry_attempts=2,
        memory_size=2048, # MB
        ephemeral_storage_size=Size.mebibytes(10240),
    )

    p4s3_job = stepfn_tasks.LambdaInvoke(stack, 'GlobalReview-PerforceHelix-To-S3-Task',
        lambda_function=p4s3_fn,
        output_path="$.Payload",
    )

    return p4s3_job


def _create_start_session_task(stack, lambda_layers, lambda_role, environment):
    with open(os.path.join(SCRIPT_DIRECTORY, '..', '..', "stepfn", "session_start", "start_session.py")) as fd:
        code = fd.read()

    instantiate_fn = aws_lambda.Function(
        stack,
        id='GlobalReview-Start-Session',
        function_name='GlobalReview-Start-Session',
        runtime=aws_lambda.Runtime.PYTHON_3_13,
        handler='index.lambda_handler',
        role=lambda_role,
        code=aws_lambda.Code.from_inline(code),
        timeout=Duration.seconds(360),
        layers=lambda_layers,
        environment=environment,
        retry_attempts=0,
        memory_size=1024, # MB
    )

    instantiate_job = stepfn_tasks.LambdaInvoke(stack, 'GlobalReview-Start-Session-Task',
        lambda_function=instantiate_fn,
        output_path="$.Payload",
    )

    return instantiate_job


def _create_is_session_public_task(stack, lambda_layers, lambda_role, environment):
    with open(os.path.join(SCRIPT_DIRECTORY, '..', '..', "stepfn", "session_start", "is_session_public.py")) as fd:
        code = fd.read()

    public_fn = aws_lambda.Function(
        stack,
        id='GlobalReview-Is-Session-Public',
        function_name='GlobalReview-Is-Session-Public', 
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

    public_job = stepfn_tasks.LambdaInvoke(stack, "GlobalReview-Is-Session-Public-Task",
        lambda_function=public_fn,
        output_path="$.Payload",
    )

    return public_job


def _create_distribution_task(stack, lambda_layers, lambda_role, environment):
    with open(os.path.join(SCRIPT_DIRECTORY, '..', '..', "stepfn", "session_start", "create_cloudfront_distribution.py")) as fd:
        code = fd.read()

    dist_fn = aws_lambda.Function(
        stack,
        id='GlobalReview-Create-Distribution',
        function_name='GlobalReview-Create-Distribution', 
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

    dist_job = stepfn_tasks.LambdaInvoke(stack, "GlobalReview-Create-Distribution-Task",
        lambda_function=dist_fn,
        output_path="$.Payload",
    )

    return dist_job


def _create_schedule_remove_stream_copy_task(stack, lambda_layers, lambda_role, environment):
    with open(os.path.join(SCRIPT_DIRECTORY, '..', '..', "stepfn", "session_start", "schedule_stream_removal.py")) as fd:
        code = fd.read()

    rmcp_fn = aws_lambda.Function(
        stack,
        id='GlobalReview-Schedule-Remove-Stream-Copy',
        function_name='GlobalReview-Schedule-Remove-Stream-Copy',
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

    rmcp_job = stepfn_tasks.LambdaInvoke(stack, 'GlobalReview-Schedule-Remove-Stream-Copy-Task',
        lambda_function=rmcp_fn,
        output_path="$.Payload",
    )

    return rmcp_job


def _create_schedule_termination_task(stack, lambda_layers, lambda_role, environment):
    with open(os.path.join(SCRIPT_DIRECTORY, '..', '..', "stepfn", "session_start", "schedule_termination.py")) as fd:
        code = fd.read()

    terminate_fn = aws_lambda.Function(
        stack,
        id='GlobalReview-Schedule-Termination',
        function_name='GlobalReview-Schedule-Termination',
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

    terminate_job = stepfn_tasks.LambdaInvoke(stack, 'GlobalReview-Schedule-Termination-Task',
        lambda_function=terminate_fn,
        output_path="$.Payload",
    )

    return terminate_job


def _create_schedule_remove_distribution_task(stack, lambda_layers, lambda_role, environment):
    with open(os.path.join(SCRIPT_DIRECTORY, '..', '..', "stepfn", "session_start", "schedule_remove_distribution.py")) as fd:
        code = fd.read()

    rmcf_fn = aws_lambda.Function(
        stack,
        id='GlobalReview-Schedule-Remove-Distribution',
        function_name='GlobalReview-Schedule-Remove-Distribution',
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

    rmcf_job = stepfn_tasks.LambdaInvoke(stack, 'GlobalReview-Schedule-Remove-Distribution-Task',
        lambda_function=rmcf_fn,
        output_path="$.Payload",
    )

    return rmcf_job


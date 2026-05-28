# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os

from constructs import Construct
from aws_cdk import (
    Duration,
    aws_apigateway as apigw,
    aws_iam as iam,
    aws_lambda,
    RemovalPolicy,
)
import cdk_nag as nag

from .cdk_lambda_layer_builder.constructs import BuildPyLayerAsset


SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


def create_fastapi_uvicorn_mangum_layer(stack) -> aws_lambda.LayerVersion:

    # create the pipy layer
    # pydantic is architecture dependent
    layer_asset = BuildPyLayerAsset.from_pypi(stack, 'GlobalReview-FastAPI-Uvicorn-Mangum-Layer-Asset',
        pypi_requirements=[
            'fastapi==0.115.11', 
            'uvicorn==0.34.0', 
            'mangum==0.19.0', 
            'python-multipart==0.0.20', 
            'python-dotenv==1.0.1',
            'fastapi-cognito==2.8.0',
            'pydantic-settings==2.8.1',
            'requests==2.29.0',  # botocore does not support urllib3 v2, use older requests lib
        ],
        py_runtime=aws_lambda.Runtime.PYTHON_3_13,
        platform="linux/amd64",
    )
    layer = aws_lambda.LayerVersion(
        stack,
        id='GlobalReview-FastAPI-Uvicorn-Mangum-Layer',
        layer_version_name='GlobalReview-FastAPI-Uvicorn-Mangum-Layer',
        code=aws_lambda.Code.from_bucket(layer_asset.asset_bucket, layer_asset.asset_key),
        compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_13],
        compatible_architectures=[aws_lambda.Architecture.X86_64],
        description ='FastAPI Python 3 modules'
    )
    return layer


def create_rest_api_lambda(
    stack,
    core_lambda_layer,
    p4_lambda_layer,
    review_lambda_layer,
    tables,
    tables_json,
    user_pool,
    user_client,
    log_group,
    schedule_stepfn,
    content_bucket,
    session_role 
):
    # api gateway lambda role
    lambda_role = iam.Role(stack, 'GlobalReview-ReST-API-Role', 
        assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
    )
    lambda_role.add_to_policy(iam.PolicyStatement(
      actions=["logs:CreateLogGroup", 
               "logs:CreateLogStream", 
               "logs:GetLogEvents",
               "logs:FilterLogEvents", 
               "logs:PutLogEvents"],
      resources=[f"arn:{stack.partition}:logs:*:{stack.account}:*"],
    ))
    lambda_role.add_to_policy(iam.PolicyStatement(
      actions=["dynamodb:ConditionCheckItem",
               "dynamodb:DescribeTable",
               "dynamodb:GetItem",
               "dynamodb:PutItem",
               "dynamodb:Query",
               "dynamodb:Scan",
               "dynamodb:UpdateItem"],
      resources= [t.table_arn for t in tables],
    ))
    lambda_role.add_to_policy(iam.PolicyStatement(
        actions=["ec2:CreateTags",
                 "ec2:DescribeImages",
                 "ec2:DescribeInstances",
                 "ec2:DescribeInstanceTypes",
                 "ec2:DescribeKeyPairs",
                 "ec2:DescribeRegions",
                 "ec2:RunInstances",
                 "ec2:TerminateInstances"],
        resources=["*"],
    ))
    lambda_role.add_to_policy(iam.PolicyStatement(
      actions=["lambda:ListFunctions",],
      resources=["*"],
    ))
    lambda_role.add_to_policy(iam.PolicyStatement(
      actions=["states:StartExecution"],
      resources=[schedule_stepfn.state_machine_arn]
    ))
    lambda_role.add_to_policy(iam.PolicyStatement(
      actions=["states:DescribeExecution"],
      resources=['*']
    ))
    lambda_role.add_to_policy(iam.PolicyStatement(
      actions=["scheduler:ListScheduleGroups", 
               "scheduler:CreateScheduleGroup",
               "scheduler:ListSchedules",
               "scheduler:GetSchedule",
               "scheduler:CreateSchedule",
               "scheduler:DeleteSchedule",],
      resources=["*"],
    ))
    lambda_role.add_to_policy(iam.PolicyStatement(
      actions=["ssm:PutParameter",
               "ssm:DeleteParameter",
               "ssm:GetParameter"],
      resources=["*"],
    ))

    nag.NagSuppressions.add_resource_suppressions(
        lambda_role,
        [
            {
                'id': "AwsSolutions-IAM5",
                'reason': ','.join(["Lambda should be able to log", 
                           "able to list lambda functions",
                           "start and describe step functions",
                           "schedule tasks",
                           "read/write to the SSM Parameter store"]),
                'applies_to': [ "Resource::*" ]
            },
        ], True
    )

    fastapi_layer = create_fastapi_uvicorn_mangum_layer(stack)

    environment = {
        "AWS_PARTITION": stack.partition,
        "COGNITO_USER_POOL_REGION": stack.cognito_auth_region,
        "COGNITO_USER_POOL_ID": user_pool.user_pool_id,
        "COGNITO_USER_POOL_CLIENT_ID": user_client.user_pool_client_id,
        "DYNAMODB_TABLES": tables_json,
        "STEPFN_SCHEDULE_SESSION_ARN": schedule_stepfn.state_machine_arn,
        "STEPFN_SCHEDULE_SESSION_NAME": schedule_stepfn.state_machine_name,
        "LOG_GROUP_NAME": log_group.log_group_name,
        "CONTENT_BUCKET_ARN": content_bucket.bucket_arn,
        "CONTENT_BUCKET_NAME": content_bucket.bucket_name,
        "SESSION_ROLE_ARN": session_role.role_arn,
        "SESSION_ROLE_NAME": session_role.role_name,
     }
     
    api_fn = aws_lambda.Function(
        stack,
        id='GlobalReview-ReST-API',
        function_name='GlobalReview-ReST-API',
        description='Global Review ReST API',
        runtime=aws_lambda.Runtime.PYTHON_3_13,
        handler='app.main.handler',
        role=lambda_role,
        code=aws_lambda.Code.from_asset(os.path.join(SCRIPT_DIRECTORY, '..', '..', 'api_gateway', 'rest_api')),
        timeout=Duration.seconds(120),
        layers=[core_lambda_layer, fastapi_layer, p4_lambda_layer, review_lambda_layer],
        retry_attempts=0,
        memory_size=2048, # MB
        environment=environment,
        tracing=aws_lambda.Tracing.PASS_THROUGH
    ) 

    return api_fn, lambda_role, fastapi_layer


def create_auth_lambda(
    stack, 
    core_lambda_layer, 
    user_pool, 
    user_client, 
):
    lambda_role = iam.Role(stack, 'GlobalReview-API-Gateway-Auth-Role', 
        assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
    )
    lambda_role.add_to_policy(iam.PolicyStatement(
      actions=["logs:CreateLogGroup", 
               "logs:CreateLogStream", 
               "logs:FilterLogEvents", 
               "logs:GetLogEvents",
               "logs:PutLogEvents"],
      resources=[f"arn:{stack.partition}:logs:*:*:*"],
    ))
    lambda_role.add_to_policy(iam.PolicyStatement(
      actions=["ssm:GetParameter",],
      resources=["*"],
    ))

    nag.NagSuppressions.add_resource_suppressions(
        lambda_role,
        [
            {
                'id': "AwsSolutions-IAM5",
                'reason': ','.join(["Lambda should be able to log", 
                           "able to list lambda functions",
                           "start and describe step functions",
                           "schedule tasks",
                           "read from the SSM Parameter store"]),
                'applies_to': [ "Resource::*" ]
            },
        ], True
    )

    environment = {
        "COGNITO_USER_POOL_ID": user_pool.user_pool_id,
        "COGNITO_USER_POOL_CLIENT_ID": user_client.user_pool_client_id,
    }

    api_fn = aws_lambda.Function(
        stack,
        id='GlobalReview-API-Gateway-Auth',
        function_name='GlobalReview-API-Gateway-Auth',
        description='Global Review Auth Structure',
        runtime=aws_lambda.Runtime.PYTHON_3_13,
        handler='handler.lambda_handler',
        role=lambda_role,
        code=aws_lambda.Code.from_asset(os.path.join(SCRIPT_DIRECTORY, '..', '..', 'api_gateway', 'amplify_auth')),
        timeout=Duration.seconds(12),
        layers=[core_lambda_layer],
        retry_attempts=0,
        memory_size=128, # MB
        environment=environment,
        tracing=aws_lambda.Tracing.PASS_THROUGH
    )

    return api_fn, lambda_role


def create_api_gateway(
    stack, 
    core_lambda_layer, 
    user_pool, 
    user_client, 
    tables, 
    tables_json,
    schedule_stepfn, 
    p4_lambda_layer, 
    review_lambda_layer,
    log_group,
    content_bucket,
    session_role
):

    rest_api_fn, rest_lambda_role, fastapi_layer = create_rest_api_lambda(
        stack,
        core_lambda_layer, p4_lambda_layer, review_lambda_layer,
        tables, tables_json,
        user_pool, user_client,
        log_group,
        schedule_stepfn,
        content_bucket,
        session_role 
    )

    auth_api_fn, auth_lambda_role = create_auth_lambda(stack, core_lambda_layer, user_pool, user_client)

    authorizer = apigw.CognitoUserPoolsAuthorizer(stack, 
        "Authorizer", 
        cognito_user_pools=[user_pool],
    )

    api = apigw.RestApi(stack, 
        'GlobalReview-API-Gateway-ReST', 
        rest_api_name='GlobalReview-API-Gateway-ReST',
        default_cors_preflight_options=apigw.CorsOptions(
            allow_origins=apigw.Cors.ALL_ORIGINS,
            allow_credentials=True,
        ),
        deploy_options=apigw.StageOptions(
            logging_level=apigw.MethodLoggingLevel.INFO,
            data_trace_enabled=True,
            tracing_enabled=True,
            access_log_destination=apigw.LogGroupLogDestination(log_group),
        ),
        cloud_watch_role=True,
        cloud_watch_role_removal_policy=RemovalPolicy.DESTROY,
        description='Global Review Gateway ReST Endpoint',
        endpoint_export_name='GlobalReview-API-Gateway-ReST'
    )

    resource = api.root.add_resource("api")

    # /api/auth
    auth_route = resource.add_resource("auth")
    auth_api_integration = apigw.LambdaIntegration(auth_api_fn)
    auth_method = auth_route.add_method("GET", auth_api_integration)

    # /api/{proxy+} 
    rest_api_integration = apigw.LambdaIntegration(rest_api_fn)
    proxy = resource.add_proxy(
       default_integration=rest_api_integration,
       any_method=True,
       default_method_options=apigw.MethodOptions(
           authorization_type=apigw.AuthorizationType.COGNITO,
           authorizer=authorizer
       )
    )

    nag.NagSuppressions.add_resource_suppressions(api, [
        {
            'id': 'AwsSolutions-APIG2',
            'reason': 'FastAPI for request validation'
        },
        {
            'id': 'AwsSolutions-APIG3',
            'reason': 'No association with WAF'
        },
        {
            "id": "AwsSolutions-APIG4",
            "reason": "Authentication done with API Gateway"
        },
        {
            "id": "AwsSolutions-IAM4",
            "reason": "API Gateway uses AWS managed role for cloud watch"
        },
    ], True)
    nag.NagSuppressions.add_stack_suppressions(stack, [
        {
            "id": "AwsSolutions-COG4",
            "reason": "Authentication done with API Gateway and Amplify"
        },
    ])

    resources = [rest_api_fn, rest_lambda_role, fastapi_layer, auth_api_fn, auth_lambda_role]

    return api, resources


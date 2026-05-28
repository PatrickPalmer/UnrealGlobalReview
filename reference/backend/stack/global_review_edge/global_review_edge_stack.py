# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os

from constructs import Construct
from aws_cdk import (
    CfnOutput,
    Duration,
    Stack,
    aws_cognito as cognito,
    aws_iam as iam,
    aws_ssm as ssm,
    aws_lambda,
    aws_lambda_nodejs as njslambda,
    RemovalPolicy,
    Tags,
)

import cdk_nag as nag


SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class GlobalReviewEdgeStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, cognito_resources=None, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # user context settings
        config = self.node.try_get_context("config")
        self.user_settings = self.node.try_get_context(config)

        # any postfix on naming
        self.postfix = '-' + self.user_settings['postfix'] if 'postfix' in self.user_settings else ""

        auth_fn, auth_role = self.create_auth_edge_function(cognito_resources['user_pool'], 
                                                            cognito_resources['user_client'], 
                                                            cognito_resources['cognito_domain'])

        self.resources = {
            'lambda_edge_auth_fn': auth_fn,
            'lambda_edge_auth_role': auth_role
        }

        # tag resources
        for resource in [ auth_fn, auth_role]:
            Tags.of(resource).add('Owner', 'GlobalReviewEdge')

        self.write_parameter_store(auth_fn)

        CfnOutput(self, 'GlobalReviewEdge-Region', 
            value=self.user_settings['edge_region'],
            description='GlobalReviewEdge deployment region',
            export_name='GlobalReviewEdge-Region',
        )

        CfnOutput(self, 'GlobalReviewEdge-AuthFn', 
            value=auth_fn.current_version.function_arn,
            description='GlobalReviewEdge Auth Function',
            export_name='GlobalReviewEdge-AuthFn',
        )


    def create_auth_edge_function(self, user_pool, user_client, cognito_domain):

        # lambda role
        lambda_role = iam.Role(self, 'GlobalReviewEdge-Edge-Role', 
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal('lambda.amazonaws.com'),
                iam.ServicePrincipal('edgelambda.amazonaws.com')
            )
        )
        lambda_role.add_to_policy(iam.PolicyStatement(
          actions=["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
          resources=[f"arn:{self.partition}:logs:*:{self.account}:*"],
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

        with open(os.path.join(SCRIPT_DIRECTORY, "..", "..", "lambda", "auth_lambda", "auth-lambda-cognito.py")) as fd:
            code = fd.read()

        # replace variables since there are no environment variables on the edge
        fmtargs = {
            "REGION": self.region,
            "ACCOUNT": self.account,
            "USER_POOL_ID": user_pool.user_pool_id,
            "USER_POOL_APP_ID": user_client.user_pool_client_id,
            "USER_POOL_DOMAIN_NAME": cognito_domain.domain_name,
            "USER_POOL_CLOUDFRONT_DOMAIN": cognito_domain.cloud_front_domain_name,
        }
        for k,v in fmtargs.items():
            code = code.replace(f'%{k.upper()}%', v)

        auth_fn = aws_lambda.Function(
            self,
            id='GlobalReviewEdge-Auth',
            function_name='GlobalReviewEdge-Auth',
            runtime=aws_lambda.Runtime.PYTHON_3_13,
            handler='index.lambda_handler',
            role=lambda_role,
            code=aws_lambda.Code.from_inline(code),
            timeout=Duration.seconds(5),
            retry_attempts=0,
            memory_size=128, # MB
        )

        """

        https://github.com/awslabs/cognito-at-edge/issues/38

        https://dev.to/aws-builders/dynamically-configure-your-lambda-edge-functions-2pkp

        auth_fn = njslambda.Function(
            self,
            id='GlobalReviewEdge-Auth',
            function_name='GlobalReviewEdge-Auth',
            runtime=aws_lambda.Runtime.NODEJS_18_X,
            handler='index.handler',
            role=lambda_role,
            entry: os.path.join(SCRIPT_DIRECTORY, "..", "..", "edge_auth", "index.js"),
            bundling={
                "node_modules": ["cognito-at-edge"]
            },
            timeout=Duration.seconds(5),
            retry_attempts=0,
            memory_size=128, # MB
        )
        """

        nag.NagSuppressions.add_resource_suppressions(auth_fn, [
            {
                "id": "AwsSolutions-L1",
                "reason": "Lambdas using Python 3.13 because of third party module pip install"
            }
        ], True)

        return auth_fn, lambda_role


    def create_rewrite_root_path_edge_function(self, user_pool, user_client, cognito_domain):

        # lambda role
        lambda_role = iam.Role(self, 'GlobalReviewEdge-RewriteRootPath-Role', 
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal('lambda.amazonaws.com'),
                iam.ServicePrincipal('edgelambda.amazonaws.com')
            )
        )
        lambda_role.add_to_policy(iam.PolicyStatement(
          actions=["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
          resources=[f"arn:{self.partition}:logs:*:{self.account}:*"],
        ))

        with open(os.path.join(SCRIPT_DIRECTORY, "..", "..", "rewrite_root_path", "rewrite_root_path.py")) as fd:
            code = fd.read()

        auth_fn = aws_lambda.Function(
            self,
            id='GlobalReviewEdge-RewriteRootPath',
            function_name='GlobalReviewEdge-RewriteRootPath',
            runtime=aws_lambda.Runtime.PYTHON_3_13,
            handler='index.lambda_handler',
            role=lambda_role,
            code=aws_lambda.Code.from_inline(code),
            timeout=Duration.seconds(2),
            retry_attempts=0,
            memory_size=128, # MB
        )

        return auth_fn, lambda_role


    def write_parameter_store(self, auth_fn):

        ssm.StringParameter(self, "GlobalReviewEdgeConfigAuthFunctionArn",
            parameter_name="/GlobalReviewEdge/Config/AuthFunctionArn",
            description="Auth Function Arn",
            string_value=auth_fn.current_version.function_arn
        )

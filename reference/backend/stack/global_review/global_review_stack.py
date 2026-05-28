# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import json

from constructs import Construct
from aws_cdk import (
    CfnOutput,
    Stack,
    aws_iam as iam,
    aws_ssm as ssm,
    aws_logs as logs,
    Tags,
)
import cdk_nag as nag

from .cdk_lambda_layer_builder.constructs import BuildPyLayerAsset

from . import (
    api_gateway, 
    cognito,
    delete_distribution_stepfn,
    dynamodb,
    lambda_layers,
    s3_buckets,
    scheduled_functions,
    schedule_session_stepfn,
    website_cdn,
)

SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class GlobalReviewStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.nag_suppression()

        # user context settings
        self.setup_user_settings()

        # any postfix on naming
        self.postfix = '-' + self.user_settings['postfix'] if 'postfix' in self.user_settings else ""

        # resources
        content_bucket = s3_buckets.create_s3_content_bucket(self)
        access_bucket = s3_buckets.create_access_log_bucket(self)

        log_group = self.create_log_group()

        # p4 layer first as it is architecture dependent
        p4_lambda_layer = lambda_layers.create_perforce_lambda_layer(self)

        core_lambda_layer = lambda_layers.create_core_lambda_layer(self)

        review_lambda_layer = lambda_layers.create_global_review_lambda_layer(self)

        term, term_role, exec_term_role = scheduled_functions.create_terminate_instance_function(self, core_lambda_layer, review_lambda_layer, log_group)

        rmcp, rmcp_role, exec_rmcp_role = scheduled_functions.create_remove_stream_copy_function(self, core_lambda_layer, review_lambda_layer, log_group)

        require_mfa = self.user_settings['require_mfa'] if 'require_mfa' in self.user_settings else False
        user_pool, user_client, cognito_domain = cognito.create_cognito_user_pool(self, mfa_required=require_mfa)

        tables, tables_json = dynamodb.create_dynamodb_tables(self)

        session_role, instance_profile = self.create_ec2_session_role(content_bucket)

        delete_dist_stepfn, delete_dist_lambda = delete_distribution_stepfn.create_delete_distribution_step_function(
            self, [core_lambda_layer, p4_lambda_layer, review_lambda_layer], 
            log_group, user_pool, user_client)

        rmcf, rmcf_role, exec_rmcf_role = scheduled_functions.create_remove_distribution_function(self, 
                                                                                    core_lambda_layer, review_lambda_layer, log_group,
                                                                                    user_pool, 
                                                                                    user_client, 
                                                                                    cognito_domain,
                                                                                    delete_dist_stepfn)

        schedule_stepfn, schedule_lambda = schedule_session_stepfn.create_schedule_session_step_function(self,
            [core_lambda_layer, p4_lambda_layer, review_lambda_layer], 
            content_bucket, tables, tables_json, log_group, session_role, instance_profile, 
            user_pool, user_client, cognito_domain)

        api, api_resources = api_gateway.create_api_gateway(self, core_lambda_layer, 
                                                        user_pool, 
                                                        user_client, 
                                                        tables, tables_json, 
                                                        schedule_stepfn, 
                                                        p4_lambda_layer, review_lambda_layer,
                                                        log_group, content_bucket, session_role)

        cdn_dist, web_bucket = website_cdn.create_website_and_cdn(self, api_gateway_rest_api=api, 
                                                           user_client=user_client, 
                                                           access_log_bucket=access_bucket)
        
        cognito.set_cognito_client_callbacks(self, user_pool=user_pool, user_client=user_client, cdn_dist=cdn_dist, lambda_layers=[core_lambda_layer])

        self.write_parameter_store(cdn_dist, web_bucket, cognito_domain)

        # tag resources
        resources = [content_bucket, access_bucket, log_group, 
                     core_lambda_layer, p4_lambda_layer, review_lambda_layer, 
                     term, term_role, exec_term_role,
                     rmcp, rmcp_role, exec_rmcp_role,
                     rmcf, rmcf_role, exec_rmcf_role,
                     api, 
                     schedule_stepfn, schedule_lambda, 
                     delete_dist_stepfn, delete_dist_lambda, 
                     user_pool, user_client, cognito_domain,
                     session_role, instance_profile,
                     web_bucket, cdn_dist]
        resources.extend(api_resources)

        for resource in resources:
            Tags.of(resource).add('Owner', 'GlobalReview')

        for table in tables:
            Tags.of(table).add('Owner', 'GlobalReview')

        self.cognito_resources = {
            'user_pool': user_pool,
            'user_client': user_client, 
            'cognito_domain': cognito_domain,
        }

        CfnOutput(self,'GlobalReview-CloudFront-DomainName',
            value=cdn_dist.domain_name,
            description='The distribution Domain Name',
            export_name='GlobalReview-Cloudfront-DomainName',
        )

        CfnOutput(self,'GlobalReview-CloudFront-URL',
            value=f"https://{cdn_dist.domain_name}",
            description='The distribution URL',
            export_name='GlobalReview-Cloudfront-URL',
        )

        CfnOutput(self, 'GlobalReview-Website-BucketName', 
            value=web_bucket.bucket_name,
            description='The name of the S3 bucket for website',
            export_name='GlobalReview-WebsiteBucketName',
        )

        CfnOutput(self, 'GlobalReview-Content-BucketName', 
            value=content_bucket.bucket_name,
            description='The name of the S3 bucket for content',
            export_name='GlobalReview-ContentBucketName',
        )

        CfnOutput(self, 'GlobalReview-AccessLog-BucketName', 
            value=access_bucket.bucket_name,
            description='The name of the S3 bucket for access logs',
            export_name='GlobalReview-AccessLogBucketName',
        )

        CfnOutput(self, 'GlobalReview-APIGatewayURL', 
            value=api.url,
            description='The API Gateway URL',
            export_name='GlobalReview-APIGatewayURL',
        )

        CfnOutput(self, 'GlobalReview-DynamoDb-Tables', 
            value=tables_json,
            description='DynamoDb Tables',
            export_name='GlobalReview-DynamoDbTables',
        )

        CfnOutput(self, 'GlobalReview-LogGroupName', 
            value=log_group.log_group_name,
            description='CloudWatch Log Group',
            export_name='GlobalReview-LogGroupName',
        )

        CfnOutput(self, 'GlobalReview-Cognito-UserPoolId', 
            value=user_pool.user_pool_id,
            description='Cognito User Pool Id',
            export_name='GlobalReview-CognitoUserPoolId',
        )

        CfnOutput(self, 'GlobalReview-Cognito-ClientId', 
            value=user_client.user_pool_client_id,
            description='Cognito Client Id',
            export_name='GlobalReview-CognitoClientId',
        )

        CfnOutput(self, 'GlobalReview-Cognito-Domain', 
            value=cognito_domain.domain_name,
            description='Cognito Domain',
            export_name='GlobalReview-CognitoDomain',
        )


    def nag_suppression(self):
        nag.NagSuppressions.add_stack_suppressions(self, [
            {
                "id": "AwsSolutions-L1",
                "reason": "Lambdas using Python 3.13 because of third party module pip install"
            },
            {
                "id": "AwsSolutions-S1",
                "reason": "S3 buckets do not need access logging"
            },
        ])


    def setup_user_settings(self):
        config = self.node.try_get_context("config")
        self.user_settings = self.node.try_get_context(config)
        self.cognito_auth_region = self.region
        

    def create_log_group(self):
        log_group = logs.LogGroup(self, "GlobalReview-LogGroup", 
            #removal_policy=RemovalPolicy.DESTROY,
        )
        return log_group


    def create_ec2_session_role(self, content_bucket):

        role = iam.Role(self, 'GlobalReview-EC2-Session-Role', 
            assumed_by=iam.ServicePrincipal('ec2.amazonaws.com'),
            managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSSMManagedInstanceCore')],
        )
        role.add_to_policy(iam.PolicyStatement(
            actions=["logs:PutLogEvents"],
            resources=[f"arn:{self.partition}:logs:*:{self.account}:*"],
        ))
        role.add_to_policy(iam.PolicyStatement(
            actions=["s3:ListBucket",
                     "s3:GetObject",
                     "s3:GetBucketLocation",],
            resources= [content_bucket.bucket_arn,
                        content_bucket.bucket_arn + "/*"]
        ))
        nag.NagSuppressions.add_resource_suppressions(
            role,
            [
                {
                    'id': "AwsSolutions-IAM4",
                    'reason': "Support SSM Managed support to EC2", 
                    'applies_to': [ "Resource::*" ]
                },
                {
                    'id': "AwsSolutions-IAM5",
                    'reason': ','.join(["Lambda should be able to log", 
                               "retrieve project from S3"]),
                    'applies_to': [ "Resource::*" ]
                },
            ], True
        )

        instance_profile = iam.CfnInstanceProfile(self, 
            "GlobalReview-Session-Instance-Profile",
            instance_profile_name="GlobalReview-Session-Instance-Profile",
            roles=[role.role_name]
        )

        return role, instance_profile


    def write_parameter_store(self, cdn_dist, web_bucket, cognito_domain):

        ssm.StringParameter(self, "GlobalReviewConfigCdnDomainName",
            parameter_name="/GlobalReview/Config/CdnDomainName",
            description="CDN Domain Name",
            string_value=cdn_dist.domain_name
        )

        ssm.StringParameter(self, "GlobalReviewConfigCdnDomainUrl",
            parameter_name="/GlobalReview/Config/CdnDomainUrl",
            description="CDN URL endpoint",
            string_value=f"https://{cdn_dist.domain_name}/"
        )

        ssm.StringParameter(self, "GlobalReviewConfigWebsiteBucketName",
            parameter_name="/GlobalReview/Config/WebsiteBucketName",
            description="S3 bucket for website",
            string_value=web_bucket.bucket_name
        )

        ssm.StringParameter(self, "GlobalReviewConfigCognitoDomainName",
            parameter_name="/GlobalReview/Config/CognitoDomainName",
            description="Cognito Domain",
            string_value=f'{cognito_domain.domain_name}.auth.{self.region}.amazoncognito.com'
        )



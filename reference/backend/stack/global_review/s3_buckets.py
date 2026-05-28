# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import (
    Duration,
    aws_s3 as s3,
    RemovalPolicy,
)
import cdk_nag as nag


def create_s3_content_bucket(stack):
    content_bucket = s3.Bucket(stack, 'GlobalReview-Content-Bucket', 
        #auto_delete_objects=True,
        block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        removal_policy=RemovalPolicy.DESTROY,
        enforce_ssl=True,
    )
    return content_bucket


def create_access_log_bucket(stack):
    bucket = s3.Bucket(stack, 'GlobalReview-Access-Log-Bucket', 
        #auto_delete_objects=True,
        block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        removal_policy=RemovalPolicy.DESTROY,
        object_ownership=s3.ObjectOwnership.OBJECT_WRITER,
        enforce_ssl=True,
        lifecycle_rules=[
            s3.LifecycleRule(
                enabled=True,
                expiration=Duration.days(1),
                noncurrent_version_expiration=Duration.days(1),
            ),
        ]
    )
    return bucket



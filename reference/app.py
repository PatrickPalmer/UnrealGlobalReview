#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
from pprint import pprint
import aws_cdk as cdk

try:
    import cdk_nag as nag
except:
    nag = None

from backend.stack.global_review_edge.global_review_edge_stack import GlobalReviewEdgeStack
from backend.stack.global_review.global_review_stack import GlobalReviewStack

SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

app = cdk.App()

config = app.node.try_get_context("config")
settings = app.node.try_get_context(config)

# validate there is a postfix
if 'postfix' not in settings or not settings['postfix']:
    raise ValueError("Configuration Settings must have a unique postfix.")
if not settings['postfix'].isalpha():
    raise ValueError("Configuration Settings postfix must be all alphabetic.")

# Deployment Environment
env_settings = {
    "account": os.getenv('CDK_DEFAULT_ACCOUNT'), 
    "region": os.getenv("CDK_DEFAULT_REGION")
}
if 'account' in settings and settings['account']:
    env_settings['account'] = settings['account']
if 'region' in settings and settings['region']:
    env_settings['region'] = settings['region']
deploy_environment = cdk.Environment(**env_settings)

review_stack = GlobalReviewStack(app, "GlobalReview-Stack", env=deploy_environment)

# Lambda @ Edge has limited deployment -- for aws partition, must be deployed in us-east-1
edge_region = 'us-east-1'
if 'edge_region' in settings and settings['edge_region']:
    edge_region = settings['edge_region']
edge_environment = cdk.Environment(account = env_settings['account'], region=edge_region)

edge_stack = GlobalReviewEdgeStack(app, "GlobalReviewEdge-Stack", env=edge_environment,
                                   cognito_resources=review_stack.cognito_resources)

if 'run_cdk_nag' in settings and settings['run_cdk_nag']:
    if nag:
        cdk.Aspects.of(app).add(nag.AwsSolutionsChecks(verbose=True))
    else:
        print("CDK NAG NOT installed")

app.synth()


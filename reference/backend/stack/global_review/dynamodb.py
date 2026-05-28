# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import json

from aws_cdk import (
    aws_dynamodb as dynamodb,
)
import cdk_nag as nag


def create_dynamodb_tables(stack):

    image_table = dynamodb.Table(stack, "GlobalReview-Image",
        partition_key=dynamodb.Attribute(name="Ami", type=dynamodb.AttributeType.STRING),
        billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        point_in_time_recovery=True,
    )

    session_table = dynamodb.Table(stack, "GlobalReview-Session",
        partition_key=dynamodb.Attribute(name="Id", type=dynamodb.AttributeType.STRING),
        billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        point_in_time_recovery=True,
    )

    stage_table = dynamodb.Table(stack, "GlobalReview-Stage",
        partition_key=dynamodb.Attribute(name="Ami", type=dynamodb.AttributeType.STRING),
        billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        point_in_time_recovery=True,
    )

    tables_json = json.dumps({
        'image': image_table.table_name,
        'session': session_table.table_name,
        'stage': stage_table.table_name,
    })

    return [image_table, session_table, stage_table], tables_json

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import copy
from globalreview.terminate import terminate_instance


# lambda hander for eventbridge scheduler callback

def lambda_handler(event, context):

    session_id = event['SessionId']
    region = event['Region']
    instance_id = event['InstanceId']

    success = terminate_instance(region, instance_id=instance_id, session_id=session_id)

    return event

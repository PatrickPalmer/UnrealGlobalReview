# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import sys
import json
import copy
import time
from globalreview.log import log_entry
import boto3


# Required input:
#   SessionId
#   S3Bucket
#   S3Prefix
#   PerforceStream

def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))

    session_id = event['SessionId'] 
    s3_bucket = event["S3Bucket"]
    s3_prefix = event["S3Prefix"]
    stream = event["PerforceStream"]

    log_entry(session_id, f"Removing Perforce Helix Stream {stream} copy.")

    s3_client = boto3.client('s3')

    # s3 list objects has 1000 object limit so need to use paginator to loop
    paginator = s3_client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=s3_bucket, Prefix=s3_prefix)

    count = 0

    delete_us = dict(Objects=[])
    for item in pages.search('Contents'):
        count += 1
        delete_us['Objects'].append(dict(Key=item['Key']))

        # flush once aws limit reached
        if len(delete_us['Objects']) >= 1000:
            try:
                s3_client.delete_objects(Bucket=s3_bucket, Delete=delete_us)
            except:
                log_entry(session_id, f"ERROR: Removing Perforce Helix Stream {stream} copy failed.")
                raise
            delete_us = dict(Objects=[])

    # flush rest
    if len(delete_us['Objects']):
        try:
            s3_client.delete_objects(Bucket=s3_bucket, Delete=delete_us)
        except:
            log_entry(session_id, f"ERROR: Removing Perforce Helix Stream {stream} copy failed.")
            raise

    log_entry(session_id, f"Removed Perforce Helix Stream {stream} copy ({count} objects).")

    return event

 
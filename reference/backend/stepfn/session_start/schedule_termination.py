# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import sys
import json
from globalreview.log import log_entry
import globalreview.terminate as terminate
from globalreview.cwprint import cwprint, cwprint_exc
import boto3
import isodate


# Required input:
#   SessionId
#   InstanceId
#   DestinationRegion
#   EndTime
#   Duration


def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))

    session_id = event['SessionId']
    region = event['DestinationRegion']
    instance_id = event['InstanceId']

    start_time = event['StartTime']
    end_time = event['EndTime']
    duration = event['Duration']

    # scheduler doesn't work with UTC notation
    if end_time.endswith('Z'):
        end_time = end_time[:-1]   

    try:
        r = terminate.create_scheduled_termination(region, instance_id, session_id, end_time)
        cwprint(r, header="Create Scheduled Termination")
    except:
        log_entry(session_id, f"ERROR: Scheduled Termination failed.")
        msg = cwprint_exc("ERROR: Scheduled Termination")
        log_entry(session_id, msg)
        raise

    log_entry(session_id, f"Scheduled Termination.")

    # schedule a second termination as an extra precaution
    et = isodate.parse_datetime(end_time)
    dur = isodate.parse_duration(duration)
    later_time = (et + dur).strftime('%Y-%m-%dT%H:%M:%S')

    r = terminate.create_scheduled_termination(region, instance_id, session_id, later_time)
    cwprint(r, header="Create Scheduled Termination")

    return event



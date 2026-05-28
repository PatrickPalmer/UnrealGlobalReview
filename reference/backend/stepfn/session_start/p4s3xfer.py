# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import tempfile
import json
import globalreview.perforce_helix as perforce
from globalreview.log import log_entry
from globalreview.cwprint import cwprint
import boto3


# install location of s3cmd using python 3 lambda layer
S3CMD_BIN = "/opt/python/lib/python3.13/site-packages/bin/s3cmd"


def get_perforce_credentials(session_id):
    # get Perforce credentials from Parameter Store
    ssm_client = boto3.client("ssm")
    try:
        response = ssm_client.get_parameter(Name=f"/GlobalReview/Perforce/{session_id}", WithDecryption=True)
    except:
        msg = f"ERROR: unable to find Perforce Helix Core credentials."
        log_entry(session_id, msg)
        raise 

    if 'Parameter' in response and 'Value' in response['Parameter']:
        value = response['Parameter']['Value']
    else:
        msg = f"ERROR: unable to retrieve Perforce Helix Core credentials."
        log_entry(session_id, msg)
        raise ValueError(msg)

    port = json.loads(value)['Port']
    user = json.loads(value)['User']
    password = json.loads(value)['Password']

    try:
        response = ssm_client.delete_parameter(Name=f"/GlobalReview/Perforce/{session_id}")
    except:
        msg = f"ERROR: unable to remove Perforce Helix Core credentials."
        log_entry(session_id, msg)
        raise 

    return port, user, password


def lambda_handler(event, context):

    session_id = event['SessionId']

    stream = event["PerforceStream"]
    s3_bucket = event["S3Bucket"]
    s3_prefix = event["S3Prefix"]

    # developer testing
    if 'SkipP4S3Copy' in event:
        return event

    port, user, password = get_perforce_credentials(session_id)

    p4 = perforce.init()

    login_results = perforce.login(p4, port, user, password)
    if login_results != "success":
        msg = f"ERROR: unable to log into Perforce Helix Core server ({port}), reason: {login_results}."
        log_entry(session_id, msg)
        raise IOError(msg)

    streams = perforce.list_streams(p4)
    cwprint(streams)
    found = False
    for s in streams:
        if 'Stream' in s and s['Stream'] == stream:
            found = True

    if not found:
        msg = f"ERROR: unable to find {stream} stream on the Perforce Helix Core server ({port})."
        log_entry(session_id, msg)
        raise ValueError(msg)

    log_entry(session_id, f"Perforce Helix Stream copy started to Amazon S3 bucket {s3_bucket}.")

    s3_client = boto3.client('s3')

    with tempfile.TemporaryDirectory() as tmpdirname:

        local_dir = os.path.join(tmpdirname, session_id)
        os.mkdir(local_dir)

        # pull copy from perforce server to local_dir
        perforce.sync_files(p4, stream, local_dir)

        perforce.logout(p4)

        s3_location = f's3://{s3_bucket}/{s3_prefix}' 
        log_entry(session_id, f"Perforce sync to Amazon S3 bucket: {s3_location}.")

        # lambda layers installed into /opt
        # optional s3cmd layer
        # @FUTURE
        #s3cmd_exists = os.path.exists(S3CMD_BIN)
        s3cmd_exists = False
        if s3cmd_exists:
            #cmd = [S3CMD_BIN, "sync", local_dir + "/", s3_location]
            #output = subprocess.check_output(cmd, text=True, shell=True)
            #cwprint(output)
            pass

        # count the files
        count = 0
        for root,dirs,files in os.walk(local_dir):
            for file in files:
                if not s3cmd_exists:
                    if root == local_dir:
                        s3_file = s3_prefix + file
                    else:
                        s3_file = s3_prefix + root[len(local_dir) + 1:] + "/" + file
                    s3_client.upload_file(os.path.join(root, file), s3_bucket, s3_file)
                count += 1

    log_entry(session_id, f"Perforce Helix Stream ({count} files) copied temporarily to Amazon S3 bucket {s3_bucket}.")

    return event


# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import sys
from .cwprint import cwprint, cwprint_exc
import platform
import traceback

try:
    from P4 import P4, P4Exception
except:
    cwprint_exc("GlobalReview.perforce_helix: ERROR: Requires p4python module.")
    P4 = None
    P4Exception = Exception


__version__ = 1.0


def init():
    if P4 is None:
        return None
    return P4()


def login(p4:P4, port:str, user:str, password:str, unicode_server:bool = False, *, level:int = 0):
    retry = False
    reason = "unknown"

    # trust file -- currently for linux
    if os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is not None:
        # lambda /tmp is the only writable directory
        os.environ["P4TRUST"] = "/tmp/.p4trust"
    elif platform.system() == 'Linux':
        os.environ["P4TRUST"]="/root/.p4trust"

    if level == 0:
        # only set once
        p4.port = port
        p4.user = user
        p4.password = password

    if unicode_server:
        p4.charset = 'utf8'

    p4.client = "GlobalReview-TMP-CLIENT"

    try:
        p4.connect()
        p4.run_login()
    except P4Exception as e:
        if 'p4 trust' in e.value:
            parts = e.value.split('\\n')
            if len(parts[3].split(':')) >= 16:
                p4.run_trust("-i", parts[3])
                retry = True
                reason = "trust"
            else:
                return "no_fingerprint"
        elif 'Authentication failed' in e.value:
            return "authentication_failed"
        elif 'Password invalid' in e.value:
            return "password_invalid"
        elif 'add SSL protocol' in e.value:
            return "requires_ssl"
        elif "server failed" in e.value:
            return "server_failed"
        elif "unicode" in e.value:
            retry = True
            reason = "invalid_unicode"
            unicode_server = not unicode_server
        else:
            cwprint_exc("Perforce Helix Login: P4Exception")
            return "unknown"
    except:
        cwprint_exc("Perforce Helix Login: Exception")
        return "unknown"

    if retry:
        if level == 0:
            # retry once
            return login(p4, port, user, password, unicode_server, level=level+1)
        else:
            return reason 
            
    return "success"


def logout(p4:P4):
    p4.disconnect()


def disconnect(p4:P4):
    p4.disconnect()


def get_info(p4:P4):
    try:
        info = p4.run_info()
    except:
        return None
    return info


def list_streams(p4:P4):
    return p4.run_streams()


def list_files(p4:P4, stream:str, filter:str = ""):
    files = p4.run_files(stream + "/...")
    if filter:
        files = [f for f in files if filter in f['depotFile']]
    return files


def sync_files(p4:P4, stream:str, output_dir:str):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    p4.run_print("-o", output_dir + "/...", stream + "/...") 
    return True


def reset_trust():
    """
    Trust certificates can change if the server changes but keeps the same IP
    Remove entries that are inhibiting login
    """
    pass



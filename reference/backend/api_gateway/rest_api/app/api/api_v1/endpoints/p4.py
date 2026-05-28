# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import traceback
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Depends, Body, Query
from fastapi_cognito import CognitoToken
from globalreview.cwprint import cwprint, cwprint_exc
import globalreview.perforce_helix as perforce


router = APIRouter()

def get_payload_user(payload):
    try: 
        port = payload['Port']
        user = payload['User']
        passwd = payload['Password']
    except:
        raise HTTPException(status_code=400, detail="payload not complete")

    return port, user, passwd


def check_stream_name(stream):
    if not stream or len(stream) < 5:
        return None

    # stream starts with //
    if not stream.startswith('//'):
        if stream[0] == '/':
            stream = '/' + stream
        else:
            stream = '//' + stream

    return stream


@router.post("/p4/streams")
async def get_streams(
    payload: dict = Body(...)
) -> Any:

    print(f"endpoint: POST /p4/streams")

    port, user, passwd = get_payload_user(payload)

    p4 = perforce.init()
    if not p4:
       raise HTTPException(status_code=500, detail="Server Perforce Helix module invalid") 

    results = perforce.login(p4, port, user, passwd)
    if results != "success":
        perforce.disconnect(p4)
        raise HTTPException(status_code=400, detail="Authentication: " + results)

    try:
        streams = perforce.list_streams(p4)
    except Exception as e:
        cwprint_exc()
        perforce.logout(p4)
        raise HTTPException(status_code=400, detail=f"failed to get streams")

    perforce.logout(p4)

    return { "streams": streams }


@router.post("/p4/streams/{stream:path}/uprojects")
async def get_uprojects(
    stream: str,
    payload: dict = Body(...)
) -> Any:

    print(f"endpoint: POST /p4/streams/{stream}/uprojects")

    port, user, passwd = get_payload_user(payload)

    stream = check_stream_name(stream)

    if not stream:
       raise HTTPException(status_code=400, detail="Stream {stream} is invalid") 

    p4 = perforce.init()
    if not p4:
       raise HTTPException(status_code=500, detail="Server Perforce Helix module invalid") 

    results = perforce.login(p4, port, user, passwd)
    if results != "success":
        perforce.disconnect(p4)
        raise HTTPException(status_code=400, detail="Authentication: " + results)

    try:
        uprojects = perforce.list_files(p4, stream, ".uproject")
    except Exception as e:
        print(e)
        cwprint_exc()
        uprojects = []

    perforce.logout(p4)

    return { "uproject": uprojects }


@router.post("/p4/streams/{stream:path}/umaps")
async def get_umaps(
    stream: str,
    payload: dict = Body(...),
    project: Optional[str] = Query("", description="filter umaps are part of project")
) -> Any:

    print(f"endpoint: POST /p4/streams/{stream}/umaps")

    port, user, passwd = get_payload_user(payload)

    stream = check_stream_name(stream)

    if not stream:
       raise HTTPException(status_code=400, detail="Stream {stream} is invalid") 

    p4 = perforce.init()
    if not p4:
       raise HTTPException(status_code=500, detail="Server Perforce Helix module invalid") 

    results = perforce.login(p4, port, user, passwd)
    if results != "success":
        perforce.disconnect(p4)
        raise HTTPException(status_code=400, detail="Authentication: " + results)

    try:
        umaps = perforce.list_files(p4, stream, ".umap")
    except Exception as e:
        print(e)
        cwprint_exc()
        umaps = []

    perforce.logout(p4)

    # filter by project
    if project:
        if project.endswith('.uproject'):
            project = '/'.join(project.split('/')[:-1])
        umaps = [u for u in umaps if u.startswith(project)]

    return { "umap": umaps }


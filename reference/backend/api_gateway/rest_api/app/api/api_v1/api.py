# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from fastapi import APIRouter

from .endpoints import config
from .endpoints import image
from .endpoints import instance
from .endpoints import keypair
from .endpoints import p4
from .endpoints import session
from .endpoints import stage


router = APIRouter()
router.include_router(config.router)
router.include_router(image.router)
router.include_router(instance.router)
router.include_router(keypair.router)
router.include_router(p4.router)
router.include_router(session.router)
router.include_router(stage.router)


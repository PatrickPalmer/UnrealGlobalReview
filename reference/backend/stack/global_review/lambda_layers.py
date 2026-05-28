# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import json

from aws_cdk import (
    aws_logs as logs,
    aws_lambda,
    Tags,
)
import cdk_nag as nag

from .cdk_lambda_layer_builder.constructs import BuildPyLayerAsset


SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


def create_core_lambda_layer(stack) -> aws_lambda.LayerVersion:
    """ Create lambda layer with a set of Python modules """

    # create the pipy layer
    layer_asset = BuildPyLayerAsset.from_pypi(stack, 'GlobalReview-core-Layer-Asset',
        pypi_requirements=['boto3', 'ksuid', 'isodate', 'crhelper'],
        py_runtime=aws_lambda.Runtime.PYTHON_3_13,
    )
    layer = aws_lambda.LayerVersion(
        stack,
        id='GlobalReview-core-Layer',
        layer_version_name='GlobalReview-core-Layer',
        code=aws_lambda.Code.from_bucket(layer_asset.asset_bucket, layer_asset.asset_key),
        compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_13],
        description ='Global Review Python 3 modules'
    )
    return layer


def create_perforce_lambda_layer(stack) -> aws_lambda.LayerVersion:
    """ Create lambda layer with Perforce Python modules """

    # create the pipy layer
    layer_asset = BuildPyLayerAsset.from_pypi(stack, 'GlobalReview-Perforce-Layer-Asset',
        pypi_requirements=['p4python',],
        py_runtime=aws_lambda.Runtime.PYTHON_3_13,
        platform="linux/amd64",
    )
    layer = aws_lambda.LayerVersion(
        stack,
        id='GlobalReview-Perforce-Layer',
        layer_version_name='GlobalReview-Perforce-Layer',
        code=aws_lambda.Code.from_bucket(layer_asset.asset_bucket, layer_asset.asset_key),
        compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_13],
        compatible_architectures=[aws_lambda.Architecture.X86_64],
        description ='Perforce Helix Python 3 modules'
    )
    return layer


def create_global_review_lambda_layer(stack) -> aws_lambda.LayerVersion:
    module_layer_asset = BuildPyLayerAsset.from_modules(stack, 'GlobalReview-Module-LayerAsset',
        local_module_dirs=[os.path.join(SCRIPT_DIRECTORY, '..', '..', 'core', 'globalreview')],
        py_runtime=aws_lambda.Runtime.PYTHON_3_13,
    )
    module_layer = aws_lambda.LayerVersion(
        stack,
        id='GlobalReview-Module-Layer',
        layer_version_name='GlobalReview-Module-Layer',
        code=aws_lambda.Code.from_bucket(module_layer_asset.asset_bucket, module_layer_asset.asset_key),
        compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_13],
        description ='GlobalReview custom Python module',
    )
    return module_layer

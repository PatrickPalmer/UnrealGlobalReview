# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import json
import boto3
from globalreview.log import log_entry
from globalreview.cwprint import cwprint, cwprint_exc


# Required input:
#   EC2 Instance Public IP Address
#   EC2 Instance Region

def lambda_handler(event, context):
 
    session_id = event['SessionId']
    instancePublicIP = event['PublicIpAddress']
    dns = event['PublicDnsName']

    # retrieve the Lambda Auth Edge function arn
    try:
        ssm_client = boto3.client('ssm')
        response = ssm_client.get_parameter(Name=f"/GlobalReviewEdge/Config/AuthFunctionArn")
        lambda_edge_auth_fn_arn = response['Parameter']['Value']
    except:
        cwprint_exc("ssm_client access")
        raise

    reference = 'Global-Review-Distribution-' + instancePublicIP
    
    # Create the CloudFront client
    cf_client = boto3.client('cloudfront')

    response = cf_client.create_distribution(
        DistributionConfig={
            'CallerReference': reference,
            'Origins': {
                'Quantity': 1,
                'Items': [
                    {
                        'Id': dns,
                        'DomainName': dns,
                        'CustomHeaders': {
                            'Quantity': 4,
                            'Items': [
                                {
                                    'HeaderName': 'COGNITO_USER_POOL_REGION',
                                    'HeaderValue': os.environ.get('COGNITO_USER_POOL_REGION')
                                },
                                {
                                    'HeaderName': 'COGNITO_USER_POOL_ID',
                                    'HeaderValue': os.environ.get('COGNITO_USER_POOL_ID')
                                },
                                {
                                    'HeaderName': 'COGNITO_USER_POOL_CLIENT_ID',
                                    'HeaderValue': os.environ.get('COGNITO_USER_POOL_CLIENT_ID')
                                },
                                {
                                    'HeaderName': 'COGNITO_USER_POOL_CLOUDFRONT_DOMAIN',
                                    'HeaderValue': os.environ.get('COGNITO_USER_POOL_CLOUDFRONT_DOMAIN')
                                },
                            ]
                        },
                        'CustomOriginConfig': {
                            'HTTPPort': 80,
                            'HTTPSPort': 443,
                            'OriginProtocolPolicy': 'http-only',
                        },
                    },
                ]
            },
            'DefaultCacheBehavior': {
                'TargetOriginId': dns,
                'ViewerProtocolPolicy': 'redirect-to-https',
                'AllowedMethods': {
                    'Quantity': 7,
                    'Items': [
                        'GET','HEAD','POST','PUT','PATCH','OPTIONS','DELETE'
                    ],
                },
                'ForwardedValues': {
                    'QueryString': False,
                    'Cookies': {
                        'Forward': 'all',
                    },
                },
                'MinTTL': 0, 
                'LambdaFunctionAssociations': {
                    'Quantity': 1,
                    'Items': [
                        {
                            'LambdaFunctionARN': lambda_edge_auth_fn_arn,
                            'EventType': 'viewer-request',
                            'IncludeBody': False
                        },
                    ]
                },
            },
            'Comment': 'Global Review distribution for individual session',
            'PriceClass': 'PriceClass_All',
            'Enabled': True,
        }
    )
    
    domain_name = response['Distribution']['DomainName']
    event['DistributionDomainName'] = domain_name
    event['DistributionId'] = response['Distribution']['Id']
    event['DistributionArn'] = response['Distribution']['ARN']

    dynamodb = boto3.resource('dynamodb')
    session_table_name = json.loads(os.environ.get("DYNAMODB_TABLES"))['session']
    sessions = dynamodb.Table(session_table_name)
    response = sessions.update_item(
        Key={'Id': session_id},
        UpdateExpression='set #SessionUrl=:1',
        ExpressionAttributeNames={
            '#SessionUrl': 'SessionUrl',
        },
        ExpressionAttributeValues={
            ':1': domain_name,
        },
        ReturnValues="UPDATED_NEW"
    )

    log_entry(session_id, f"Created Distribution ({event['DistributionId']}) endpoint at {domain_name}.")

    # tell cognito app client to authorize distribution callback
    user_pool_id = os.environ.get("COGNITO_USER_POOL_ID")
    user_pool_client_id = os.environ.get("COGNITO_USER_POOL_CLIENT_ID")

    cognito_client = boto3.client('cognito-idp')
    try:
        client = cognito_client.describe_user_pool_client(UserPoolId=user_pool_id, ClientId=user_pool_client_id)
    except:
        cwprint_exc("Cognito Describe User Pool Client")
        client = {}

    cwprint(client)

    kwargs = client['UserPoolClient']

    domain_url = f"https://{domain_name}/"
    kwargs['CallbackURLs'].append(domain_url)

    # remove Read Only fields
    del(kwargs['LastModifiedDate'])
    del(kwargs['CreationDate'])
    
    try:
        # update requires you to rewire teh entire contents, not just the changed fields
        resp = cognito_client.update_user_pool_client(**kwargs)
        log_entry(session_id, f"Update User Pool Client ({user_pool_client_id}) with {domain_name}.")
    except:
        log_entry(session_id, f"ERROR: Update User Pool Client ({user_pool_client_id}) with {domain_name} failed.")
        cwprint_exc("Cognito Update User Pool Client")
        resp = {}

    return event 

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
Limit Access to EC2
    https://aws.amazon.com/blogs/networking-and-content-delivery/limit-access-to-your-origins-using-the-aws-managed-prefix-list-for-amazon-cloudfront/

EC2 describe managed prefix lists
    https://docs.aws.amazon.com/cli/latest/reference/ec2/describe-managed-prefix-lists.html

"""

from globalreview.log import log_entry
import boto3


# Required input:
#   SessionId
#   DestinationRegion
#   InstanceType

def lambda_handler(event, context):

    session_id = event['SessionId']
    destination_region = event['DestinationRegion']
    instance_type = event['InstanceType']

    ec2_client = boto3.client('ec2', region_name=destination_region)

    # find out if the region has the instance type
    types = ec2_client.describe_instance_types(InstanceTypes=[instance_type])
    if len(types['InstanceTypes']) == 0:
        msg = f"ERROR: Instance Type {instance_type} not supported in {destination_region} region."
        log_entry(session_id, msg)
        raise ValueError(msg)

    # find out which availability zones have the instance type
    offerings = ec2_client.describe_instance_type_offerings(LocationType="availability-zone", 
        Filters=[{
            'Name':'instance-type',
            'Values': [instance_type],
        }]
    )
    zones = [o['Location'] for o in offerings['InstanceTypeOfferings']]

    vpcs = ec2_client.describe_vpcs(Filters=[{
        'Name':'is-default',
        'Values': ['true']},
    ])['Vpcs'] 

    if len(vpcs) == 0:
        msg = f"ERROR: default VPC not found in {destination_region} region."
        log_entry(session_id, msg)
        raise ValueError(msg)

    log_entry(session_id, f"Using default VPC ({vpcs[0]['VpcId']}) in {destination_region}.")
    
    # subnets in vpc that are public
    subnets = ec2_client.describe_subnets(Filters=[
        {
            'Name': 'vpc-id',
            'Values': [vpcs[0]['VpcId']]
        },
        {
            'Name': 'map-public-ip-on-launch',
            'Values': ['true']
        }
    ])['Subnets']
    
    if len(subnets) == 0:
        msg = f"ERROR: default Public Subnet not found in {destination_region} region."
        log_entry(session_id, msg)
        raise ValueError(msg)

    # find a subnet with instance type available
    subnet_index = None
    for idx,subnet in enumerate(subnets):
        if subnet['AvailabilityZone'] in zones:
            subnet_index = idx
            break 

    if subnet_index is None:
        msg = f"ERROR: Instance Type {instance_type} not supported any public subnets in {destination_region} region."
        log_entry(session_id, msg)
        raise ValueError(msg)

    log_entry(session_id, f"Using default Public Subnet ({subnets[subnet_index]['SubnetId']}) in {destination_region}.")
    
    # subnets in vpc that are public
    sgs = ec2_client.describe_security_groups(Filters=[
        {
            'Name': 'tag:Name',
            'Values': ["GlobalReview-Session-EC2-Security-Group"],
        }
    ])['SecurityGroups']
    
    if not isinstance(sgs, list) or len(sgs) == 0:

        # Retrieving the CloudFront managed prefix list ID
        # Only allow access to this security grou from CloudFront 
        response = ec2_client.describe_managed_prefix_lists(
            Filters=[
                {
                    'Name': 'prefix-list-name',
                    'Values': ['com.amazonaws.global.cloudfront.origin-facing']
                }
            ]
        )
        prefix_list_id = response['PrefixLists'][0]['PrefixListId']

        # create a security group with needed access
        sg = ec2_client.create_security_group(
            Description='GlobalReview Security Group for Session EC2s',
            GroupName='GlobalReview-Session-EC2-Security-Group',
            VpcId=vpcs[0]['VpcId'],
        )

        rules = [
                {
                    'FromPort': 80,
                    'ToPort': 80,
                    'IpProtocol': 'tcp',
                    #'IpRanges': [{'CidrIp': '0.0.0.0/0'}],
                    'PrefixListIds': [{'PrefixListId': prefix_list_id}]
                },
                {
                    'FromPort': 8888,
                    'ToPort': 8888,
                    'IpProtocol': 'tcp',
                    #'IpRanges': [{'CidrIp': '0.0.0.0/0'}],
                    'PrefixListIds': [{'PrefixListId': prefix_list_id}]
                },
                {
                    'FromPort': 8888,
                    'ToPort': 8888,
                    'IpProtocol': 'udp',
                    #'IpRanges': [{'CidrIp': '0.0.0.0/0'}],
                    'PrefixListIds': [{'PrefixListId': prefix_list_id}]
                }
        ]    

        # First try to create 3 rules to limit the port access
        # by default, an account does not have enough rule quotas to support
        # this, but attempt anyways if the account has had the quotas increased
        try:
            response = ec2_client.authorize_security_group_ingress(
                GroupId=sg['GroupId'],
                IpPermissions=rules
            )
        except:
            # ok, reached quota limit
            # create a single rule with more of a port range supporting both tcp and udp
            response = ec2_client.authorize_security_group_ingress(
                GroupId=sg['GroupId'],
                IpPermissions=[{
                    'FromPort': 80,
                    'ToPort': 8888,
                    'IpProtocol': '-1',
                    'PrefixListIds': [{'PrefixListId': prefix_list_id}]
                }]
            )

        # tag it 
        ec2_client.create_tags(
            Resources=[sg['GroupId']],
            Tags=[
                {"Key": "Name", "Value": "GlobalReview-Session-EC2-Security-Group"},
                {"Key": "GlobalReview", "Value": 'true'},
            ]
        )
        
        log_entry(session_id, f"Created Security Group ({sg['GroupId']}) in {destination_region}.")
    else:
        sg = sgs[0]
        log_entry(session_id, f"Using Security Group ({sg['GroupId']}) in {destination_region}.")
        
    log_entry(session_id, f"Using Availability Zone ({subnets[subnet_index]['AvailabilityZone']}) in {destination_region}.")
        
    event.update({
        'StatusCode': 200,
        'VpcId': vpcs[0]['VpcId'],
        'SubnetId': subnets[subnet_index]['SubnetId'],
        'SecurityGroupId': sg['GroupId'],
        'AvailabilityZone': subnets[subnet_index]['AvailabilityZone'],
        'AvailabilityZoneId': subnets[subnet_index]['AvailabilityZoneId'],
    })
    
    return event

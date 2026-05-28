# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import json
from globalreview.log import log_entry
import boto3


USERDATA = """version: 1.0
tasks:
- task: initializeVolume
  inputs:
    initialize: all
- task: executeScript
  inputs:
  - frequency: always
    type: batch
    detach: true
    runAs: admin
    content: |-

      :: install aws.exe
      msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi /qn

      :: install boto3 into Unreal Engine's python
      {UnrealInstallDir}/Engine/Binaries/ThirdParty/Python3/Win64/python.exe -m pip install boto3  >> C:/Windows/Temp/GlobalReview.log

      :: Create LogMessage.py to log messages to cloudfront
      {UnrealInstallDir}/Engine/Binaries/ThirdParty/Python3/Win64/python.exe -c "p='''import sys,json,datetime,time,boto3;lc = boto3.client('logs', region_name='{SourceRegion}');ts = int(round(time.time() * 1000));logs = lc.put_log_events(logGroupName='{LogGroupName}', logStreamName='{LogStreamName}', logEvents=[{{'timestamp':ts, 'message': json.dumps({{ 'Id': '{SessionId}', 'CreateTime': datetime.datetime.now().isoformat(), 'Message':sys.argv[1] }}) }}])''';fd = open('c:/Windows/Temp/LogMessage.py','w');fd.write(p);fd.close()"

      {UnrealInstallDir}/Engine/Binaries/ThirdParty/Python3/Win64/python.exe C:/Windows/Temp/LogMessage.py "Session: EC2 Starting."

      {UnrealInstallDir}/Engine/Binaries/ThirdParty/Python3/Win64/python.exe C:/Windows/Temp/LogMessage.py "Session: Installing WebRTC server."

      cmd /c "{UnrealInstallDir}/Engine/Plugins/Media/PixelStreaming/Resources/WebServers/get_ps_servers.bat" >> C:/Windows/Temp/GlobalReview.log

      cmd /c "{UnrealInstallDir}/Engine/Plugins/Media/PixelStreaming/Resources/WebServers/SignallingWebServer/platform_scripts/cmd/setup.bat"  >> C:/Windows/Temp/GlobalReview.log

      :: turn off Windows Firewall as not to intefere with communications with cloudfront
      netsh advfirewall set allprofiles state off  >> C:/Windows/Temp/GlobalReview.log

      {UnrealInstallDir}/Engine/Binaries/ThirdParty/Python3/Win64/python.exe C:/Windows/Temp/LogMessage.py "Session: Starting Project S3 download."

      :: configure S3 to use crt transfer client for faster throughput
      "C:/Program Files/Amazon/AWSCLIV2/aws.exe" configure set s3.preferred_transfer_client crt
      "C:/Program Files/Amazon/AWSCLIV2/aws.exe" configure set s3.target_bandwidth 10GB/s

      "C:/Program Files/Amazon/AWSCLIV2/aws.exe" s3 cp s3://{S3Bucket}/{S3Prefix} {ProjectDir} --recursive --region {SourceRegion} 2>&1 >> C:/Windows/Temp/GlobalReview.log

      {UnrealInstallDir}/Engine/Binaries/ThirdParty/Python3/Win64/python.exe C:/Windows/Temp/LogMessage.py "Session: Project S3 download completed."

      :: Checking for PixelStreaming Plugin
      {UnrealInstallDir}/Engine/Binaries/ThirdParty/Python3/Win64/python.exe -c "import sys,json,subprocess;fd = open('{UnrealLocalProject}');js = json.load(fd); fd.close(); plugins = js['Plugins'] if 'Plugins' in js else []; exists = any([p['Name'] == 'PixelStreaming' and p['Enabled'] == True for p in plugins]); msg = 'Unreal PixelStreaming plugin enabled.' if exists else 'Warning: Unreal Project missing required PixelStreaming plugin.'; subprocess.run(['{UnrealInstallDir}/Engine/Binaries/ThirdParty/Python3/Win64/python.exe', 'C:/Windows/Temp/LogMessage.py', msg]); plugins = [p for p in plugins if p['Name'] != 'PixelStreaming']; plugins.append({{'Name': 'PixelStreaming', 'Enabled': True}}); js['Plugins'] = plugins; fd = open('{UnrealLocalProject}', 'w'); json.dump(js, fd, indent=8); fd.close()"

      {UnrealInstallDir}/Engine/Binaries/ThirdParty/Python3/Win64/python.exe C:/Windows/Temp/LogMessage.py "Session: Starting Unreal Editor."

      start /B {UnrealInstallDir}/Engine/Binaries/Win64/UnrealEditor-Cmd.exe "{UnrealLocalProject}" "{UnrealLevelGame}" -EditorPixelStreamingRes={RenderWidth}x{RenderHeight} -EditorPixelStreamingStartOnLaunch=true -PixelStreamingIP=localhost -PixelStreamingPort=8888 -RenderOffScreen -Unattended -Windowed -WinX=0 -WinY=0 -ForceRes -EditorPixelStreamingResX={RenderWidth} -EditorPixelStreamingResY={RenderHeight} -ResX={RenderWidth} -ResY={RenderHeight} -EditorPixelStreamingUseRemoteSignallingServer=true {PixelStreamHMDOption} {UnrealRenderingAPI} -nohdr -game -CrashReports -FullStdOutLogOutput -AllowPixelStreamingCommands >> C:/Windows/Temp/GlobalReview-UnrealEditor.log

      {UnrealInstallDir}/Engine/Binaries/ThirdParty/Python3/Win64/python.exe C:/Windows/Temp/LogMessage.py "Session: Starting Web Server."

      :LOOP
      ECHO Starting Signal Server 

      powershell -WindowStyle Hidden -file "{UnrealInstallDir}/Engine/Plugins/Media/PixelStreaming/Resources/WebServers/SignallingWebServer/platform_scripts/cmd/Start_SignallingServer.ps1" 2>&1  >> C:/Windows/Temp/GlobalReview-SignalServer.log

      ECHO ERROR Signal Server Stopped 
      GOTO LOOP

      {UnrealInstallDir}/Engine/Binaries/ThirdParty/Python3/Win64/python.exe C:/Windows/Temp/LogMessage.py "Session: Unreal Editor stopped."

"""


# Required input:
#   SessionId
#   DestinationAmi
#   VpcId
#   SubnetId
#   SecurityGroupId
#   InstanceType
#   AvailabilityZone
#   KeyName

def lambda_handler(event, context):

    source_region = os.environ.get('AWS_REGION')
    event['SourceRegion'] = source_region

    destination_region = str(event['DestinationRegion'])

    session_id = event['SessionId']
    ami = str(event['DestinationAmi'])
    vpc_id = event['VpcId']
    subnet_id = event['SubnetId']
    security_group_id = event['SecurityGroupId']
    instance_type = event['InstanceType']
    availability_zone = event['AvailabilityZone']
    key_name = event['KeyName'] if event['KeyName'] else None
    
    instance_profile_arn = os.environ.get('INSTANCE_PROFILE_ARN')

    ec2_client = boto3.client('ec2', region_name=destination_region)

    event['LogGroupName'] = os.environ.get("LOG_GROUP_NAME")
    event['LogStreamName'] = event['SessionId']

    # remap the Unreal Project in the Stream to the local drive
    unreal_project = event['UnrealProject']
    perforce_stream = event['PerforceStream']

    # ephemeral disk mounts as Z:
    event['ProjectDir'] = "Z:/Project"
    event['UnrealLocalProject'] = event['ProjectDir'] + "/" + unreal_project[len(perforce_stream):]
    
    # remap the Unreal Level in the Stream to the Unreal /Game Name
    unreal_level = event['UnrealLevelName']
    idx = unreal_level.index('Content') + len('Content')
    event['UnrealLevelGame'] = "/Game" + unreal_level[idx:]

    # Render resolution - default 1080p
    if 'RenderWidth' not in event or 'RenderHeight' not in event:
        event['RenderWidth'] = 1920
        event['RenderHeight'] = 1080

    event['PixelStreamHMDOption'] = "-PixelStreamingEnableHMD" if 'PixelStreamHMD' in event and event['PixelStreamHMD'] else ""

    event['UnrealRenderingAPI'] = ""
    if 'RenderingAPI' in event:
        if event['RenderingAPI'] == 'dx11':
            event['UnrealRenderingAPI'] = '-d3d11'
        elif event['RenderingAPI'] == 'dx12':
            event['UnrealRenderingAPI'] = '-d3d12'
        elif event['RenderingAPI'] == 'vulkan':
            event['UnrealRenderingAPI'] = '-vulkan'

    kwargs = {}
    if key_name:
        kwargs['KeyName'] = key_name
    try:
        response = ec2_client.run_instances(
            ImageId=ami,
            InstanceType=instance_type,
            Placement={
                'AvailabilityZone': availability_zone,
            },
            SecurityGroupIds=[security_group_id],
            SubnetId=subnet_id,
            UserData=USERDATA.format(**event),
            MinCount=1,
            MaxCount=1,
            IamInstanceProfile={ 'Arn': instance_profile_arn, },
            MetadataOptions={
                'HttpTokens': 'required',
                'HttpPutResponseHopLimit': 4,
            },
            **kwargs
        )
    except Exception as e:
        log_entry(session_id, f"ERROR: Unable to launch instance (AMI {ami}) in {destination_region} region.")
        log_entry(session_id, f"ERROR: Exception:({e}).")
        raise

    instance = response['Instances'][0]

    log_entry(session_id, f"Launched instance ({instance['InstanceId']}, AMI {ami}) in {destination_region} region.")

    ec2_client.create_tags(
            Resources=[instance['InstanceId']],
            Tags=[
                {
                    'Key': 'GlobalReview',
                    'Value': 'true'
                },
                {
                    'Key': 'Name',
                    'Value': f'GlobalReview-Session-{session_id}'
                },
            ]
        )
    
    dynamodb = boto3.resource('dynamodb')
    session_table_name = json.loads(os.environ.get("DYNAMODB_TABLES"))['session']
    sessions = dynamodb.Table(session_table_name)
    response = sessions.update_item(
        Key={'Id': session_id},
        UpdateExpression='set #InstanceId=:1',
        ExpressionAttributeNames={
            '#InstanceId': 'InstanceId',
        },
        ExpressionAttributeValues={
            ':1': instance['InstanceId'],
        },
        ReturnValues="UPDATED_NEW"
    )
    
    event.update({
        'InstanceId': instance['InstanceId'],
    })

    return event

 

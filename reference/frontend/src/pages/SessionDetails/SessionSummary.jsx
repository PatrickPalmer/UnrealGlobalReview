// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React, { useState, useEffect } from 'react';
import {
  Box,
  ColumnLayout,
  Container,
  Header,
  Spinner,
  Button,
  SpaceBetween,
} from '@cloudscape-design/components';
import ProcessStatusIndicator from '../../components/ProcessStatusIndicator';
import { formatIsoDuration, formatIso8601 } from '../../common/format';
import CopyText from '../../common/copy-text';

const SessionSummary = ({session, status, onRefreshClick, loading}) => {

  const onRefresh = event => {
    event.preventDefault();
    onRefreshClick();
  };

  const header = (<Header 
                    variant="h2"
                    actions={
                      <SpaceBetween direction="horizontal" size="xs">
                        <Button disabled={loading} onClick={onRefresh} iconName="refresh"/>
                      </SpaceBetween>
                    }>
                    Session Summary
                    </Header>);

  return (
    <Container header={header}>
      <SpaceBetween direction="vertical" size="xxl">
      <ColumnLayout columns={4} variant="text-grid">
        <div>
          <Box variant="awsui-key-label">Name</Box>
          <div>
            {loading ? <Spinner/> : session['Name'] ? session['Name'] : "Global Review Session"}
          </div>
        </div>
        <div>
          <Box variant="awsui-key-label">Region</Box>
          <div>
            {loading ? <Spinner/> : session['Region']}
          </div>
        </div>
        <div>
          <Box variant="awsui-key-label">Instance Type</Box>
          <div>
            {loading ? <Spinner/> : session['InstanceType']}
          </div>
        </div>
        <div>
          <Box variant="awsui-key-label">Process Status</Box>
          <div>
            {loading ? <Spinner/> : <ProcessStatusIndicator status={status}/>}
          </div>
        </div>
      </ColumnLayout>
      <ColumnLayout columns={4} variant="text-grid">
        <div>
          <Box variant="awsui-key-label">Session ID</Box>
          <div>
            {loading ? <Spinner/> : session['Id']}
          </div>
        </div>
        <div>
          <Box variant="awsui-key-label">Created</Box>
          <div>
            {loading ? <Spinner/> : formatIso8601(session['CreateTime'])}
          </div>
        </div>
        <div>
          <Box variant="awsui-key-label">End Time</Box>
          <div>
          {loading ? <Spinner/> : (formatIso8601(session['EndTime']) + " (" + formatIsoDuration(session['Duration']) + ")")}
          </div>
        </div>
        <div>
          <Box variant="awsui-key-label">Instance Id</Box>
          <div>
            {loading ? <Spinner/> : session['InstanceId'] ? session['InstanceId'] : '?'}
          </div>
        </div>
      </ColumnLayout>
      <ColumnLayout columns={4} variant="text-grid">
        <div>
          <Box variant="awsui-key-label">Session URL</Box>
          <div>
            {loading && <Spinner/>}
            {(!loading && !session['SessionUrl']) && '?'}
            {(!loading && session['SessionUrl']) && 
            <CopyText
              copyText={"https://" + session['SessionUrl'] + "/"}
              copyButtonLabel="Copy URL"
              successText="URL copied"
              errorText="URL failed to copy"
            />
            }
          </div>
        </div>
        <div>
          <Box variant="awsui-key-label">Perforce Stream</Box>
          <div>
            {loading ? <Spinner/> : session['PerforceStream']}
          </div>
        </div>
        <div>
          <Box variant="awsui-key-label">Unreal Engine Level</Box>
          <div>
          {loading ? <Spinner/> : session['UnrealLevelName']}
          </div>
        </div>
        <div>
          <Box variant="awsui-key-label">AMI ID</Box>
          <div>
            {loading ? <Spinner/> : session['Ami']}
          </div>
        </div>
        <div>
          <Box variant="awsui-key-label">Description</Box>
          <div>
            {loading ? <Spinner/> : session['Description']}
          </div>
        </div>
      </ColumnLayout>
      </SpaceBetween>
    </Container>
  );
}

export default SessionSummary;

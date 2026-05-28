// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React from 'react';
import {
  Box,
  Button,
  ColumnLayout,
  Container,
  Header,
  SpaceBetween,
} from '@cloudscape-design/components';
import { DEFAULT_STEP_INFO } from '../steps-config';
import { checkSessionDetails } from '../index';

const Review = ({ info: { engine, details }, setActiveStepIndex }) => {

  const missing_style = {
    color: 'red',
    'font-style': 'italic'
  };

  return (
    <Box margin={{ bottom: 'l' }}>
      <SpaceBetween size="xxl">
        <SpaceBetween size="xs" className="step-1-review">
          <Header
            variant="h3"
            headingTagOverride="h2"
            actions={
              <Button className="edit-step-btn" onClick={() => setActiveStepIndex(0)}>
                Edit
              </Button>
            }
          >
            Step 1: Session details
          </Header>

          <SpaceBetween size="l">
            <Container>
              <ColumnLayout columns={2} variant="text-grid">

                <div>
                  <Box variant="awsui-key-label">Name</Box>
                  {details.sessionName ? (
                    <div>{details.sessionName}</div>
                  ) : (
                    <div style={missing_style}>missing session name</div>
                 )}
                </div>

                {details.instanceClass ? (
                  <div>
                    <Box variant="awsui-key-label">Instance Type</Box>
                    <div>{details.instanceClass.label}</div>
                  </div>
                ) : (
                  <div>
                    <Box variant="awsui-key-label">Instance Type</Box>
                    <div style={missing_style}>missing instance class</div>
                  </div>
                )}

                <div>
                  <Box variant="awsui-key-label">Region</Box>
                  {details.region ? (
                    <div>{details.region.label}</div>
                  ) : (
                    <div style={missing_style}>missing region</div>
                )}
                </div>

                {details.ami ? (
                  <div>
                    <Box variant="awsui-key-label">AMI</Box>
                    <div>{details.ami.label}</div>
                  </div>
                ) : (
                  <div>
                    <Box variant="awsui-key-label">AMI</Box>
                    <div style={missing_style}>missing AMI</div>
                  </div>
                )}

                {details.keypair ? (
                  <div>
                    <Box variant="awsui-key-label">Key pair</Box>
                    <div>{details.keypair.label}</div>
                  </div>
                ) : (
                  <div>
                    <Box variant="awsui-key-label">Key pair</Box>
                    <div>None</div>
                  </div>
                )}

                {details.duration ? (
                  <div>
                    <Box variant="awsui-key-label">Duration</Box>
                    <div>{details.duration.label}</div>
                  </div>
                ) : (
                  <div>
                    <Box variant="awsui-key-label">Duration</Box>
                    <div style={missing_style}>missing duration</div>
                  </div>
                )}

                <div>
                  <Box variant="awsui-key-label">Description</Box>
                  <div>{details.description}</div>
                </div>
              </ColumnLayout>
            </Container>
          </SpaceBetween>
        </SpaceBetween>
        <SpaceBetween size="xs" className="step-2-review">
          <Header
            variant="h3"
            headingTagOverride="h2"
            actions={
              <Button className="edit-step-btn" onClick={() => setActiveStepIndex(1)}>
                Edit
              </Button>
            }
          >
            Step 2: Perforce Helix details
          </Header>
          <Container>
            <ColumnLayout columns={2} variant="text-grid">
              {engine.username === '' ? (
                <div>
                  <Box variant="awsui-key-label">User</Box>
                  <div style={missing_style}>missing Perforce Helix user name</div>
                </div>
              ) : (
                <div>
                  <Box variant="awsui-key-label">User</Box>
                  <div>{engine.username}</div>
                </div>
              )}

              {engine.port === '' ? (
                <div>
                  <Box variant="awsui-key-label">Port</Box>
                  <div style={missing_style}>missing Perforce Helix port</div>
                </div>
              ) : (
                <div>
                  <Box variant="awsui-key-label">Port</Box>
                  <div>{engine.port}</div>
                </div>
              )}

              {engine.stream ? (
                <div>
                  <Box variant="awsui-key-label">Stream</Box>
                  <div>{engine.stream.label}</div>
                </div>
              ) : (
                <div>
                  <Box variant="awsui-key-label">Stream</Box>
                  <div style={missing_style}>missing stream</div>
                </div>
              )}

              {engine.uproject ? (
                <div>
                  <Box variant="awsui-key-label">Unreal Engine Project</Box>
                  <div>{engine.uproject.value}</div>
                </div>
              ) : (
                <div>
                  <Box variant="awsui-key-label">Unreal Engine Project</Box>
                  <div style={missing_style}>missing project</div>
                </div>
              )}

              {engine.umap ? (
                <div>
                  <Box variant="awsui-key-label">Unreal Engine Level</Box>
                  <div>{engine.umap.value}</div>
                </div>
              ) : (
                <div>
                  <Box variant="awsui-key-label">Unreal Engine Level</Box>
                  <div style={missing_style}>missing level</div>
                </div>
              )}

            </ColumnLayout>
          </Container>
        </SpaceBetween>
      </SpaceBetween>
    </Box>
  );
};

export default Review;
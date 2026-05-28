// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React from 'react';
import { BreadcrumbGroup, Button, HelpPanel, SpaceBetween } from '@cloudscape-design/components';
import { useNavigate } from 'react-router-dom';
import { PageHeader } from '../common/common-components';
import { Auth } from 'aws-amplify';


export const Breadcrumbs = () => (
  <BreadcrumbGroup 
    items={[{text: 'Global Review', href: '/sessions'}]} 
    expandAriaLabel="Show path" 
    ariaLabel="Breadcrumbs" />
);


export const FullPageHeader = ({
  resourceName = 'Sessions',
  extraActions = null,
  ...props
}) => {
  const isOnlyOneSelected = props.selectedItems.length === 1;

  const navigate = useNavigate();

  const onCreateClick = event => {
    event.preventDefault();
    navigate("/createSession/")
  };

  const onLogoutClick = event => {
    event.preventDefault();
    Auth.signOut();
  };

  return (
    <PageHeader
      variant="awsui-h1-sticky"
      title={resourceName}
      actionButtons={
        <SpaceBetween size="xs" direction="horizontal">
          {extraActions}
          <Button 
            data-testid="header-btn-create"
            variant="primary"
            onClick={onCreateClick}>
            Create Session
          </Button>
          <Button 
           data-testid="header-btn-logout" 
           onClick={onLogoutClick}>
            Logout
          </Button>
        </SpaceBetween>
      }
      {...props}
    />
  );
};

export const ToolsContent = () => (
  <HelpPanel header={<h2>Sessions</h2>}>
    <p>
      View your active sessions. To drill down even further into the details, 
      choose the name of an individual session.<br></br><br></br>
      To see all active and inactive sessions, click the All Sessions checkbox. <br></br><br></br>
      To start a new Global Review session, click Create Session.
    </p>
  </HelpPanel>
);



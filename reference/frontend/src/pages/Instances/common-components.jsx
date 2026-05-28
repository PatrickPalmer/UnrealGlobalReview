// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React from 'react';
import { BreadcrumbGroup, Button, HelpPanel, SpaceBetween } from '@cloudscape-design/components';
import { useNavigate } from 'react-router-dom';
import { PageHeader } from '../common/common-components';
import { Auth } from 'aws-amplify';


export const Breadcrumbs = () => (
  <BreadcrumbGroup 
    items={[{text: 'Global Review', href: '/instances'}]} 
    expandAriaLabel="Show path" 
    ariaLabel="Breadcrumbs" />
);


export const FullPageHeader = ({
  resourceName = 'Instances',
  extraActions = null,
  ...props
}) => {
  const isOnlyOneSelected = props.selectedItems.length === 1;

  const navigate = useNavigate();

  const onTerminateClick = event => {
    event.preventDefault();
    props.onTerminateCallback();
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
            disabled={!props.terminateEnabled}
            onClick={onTerminateClick}>
            Terminate Instance
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
  <HelpPanel header={<h2>Instances</h2>}>
    <p>
      View your active instances.<br></br><br></br>
      To terminate one of your global review instances, click Terminate Instance.  
    </p>
  </HelpPanel>
);



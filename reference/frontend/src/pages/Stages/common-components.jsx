// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React from 'react';
import { BreadcrumbGroup, Button, HelpPanel, SpaceBetween } from '@cloudscape-design/components';
import { PageHeader } from '../common/common-components';
import { Auth } from 'aws-amplify';

export const Breadcrumbs = () => (
  <BreadcrumbGroup 
    items={[{text: 'Global Review', href: '/stages'}]} 
    expandAriaLabel="Show path" 
    ariaLabel="Breadcrumbs" />
);

export const FullPageHeader = ({
  resourceName = 'Stages',
  extraActions = null,
  ...props
}) => {
  const isOnlyOneSelected = props.selectedItems.length === 1;

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
  <HelpPanel header={<h2>Stages</h2>}>
    <p>
      View your staged AMIs.<br></br><br></br>
      After you start a Global Review session, a stage is created in that region. 
      Stages are reused for other review sessions in that region. 
    </p>
  </HelpPanel>
);
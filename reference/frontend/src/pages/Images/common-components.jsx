// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React from 'react';
import { BreadcrumbGroup, Button, HelpPanel, SpaceBetween } from '@cloudscape-design/components';
import { useNavigate } from 'react-router-dom';
import { PageHeader } from '../common/common-components';
import { Auth } from 'aws-amplify';


export const Breadcrumbs = () => (
  <BreadcrumbGroup 
    items={[{text: 'Global Review', href: '/images'}]} 
    expandAriaLabel="Show path" 
    ariaLabel="Breadcrumbs" />
);


export const FullPageHeader = ({
  resourceName = 'Images',
  extraActions = null,
  ...props
}) => {
  const isOnlyOneSelected = props.selectedItems.length === 1;

  const navigate = useNavigate();

  const onCreateClick = event => {
    event.preventDefault();
    props.onCreateCallback();
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
            Register Image
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
  <HelpPanel header={<h2>Images</h2>}>
    <p>
      View your registered Amazon Machine Images (AMIs).<br></br><br></br>
      After you create and register an AMI, you can use it to launch new instances. To register a new image, click Register Image.
    </p>
  </HelpPanel>
);



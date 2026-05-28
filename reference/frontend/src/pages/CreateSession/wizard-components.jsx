// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React from 'react';
import BreadcrumbGroup from '@cloudscape-design/components/breadcrumb-group';
import { useNavigate } from 'react-router-dom';

export const Breadcrumbs = () => {
  
  const navigate = useNavigate();

  const onBreadcrumbClick = event => {
    event.preventDefault();
    navigate("/sessions");
  };

  const onFollowHandler = ev => {
    ev.preventDefault();
  };

  return (
    <BreadcrumbGroup
      expandAriaLabel="Show path"
      ariaLabel="Breadcrumbs"
      onClick={onBreadcrumbClick}
      items={[
        { text: 'Sessions', href: '/sessions' },
        { text: 'Launch Global Review Instance'},
      ]}
      onFollow={onFollowHandler.bind(this)}
    />
  );
};

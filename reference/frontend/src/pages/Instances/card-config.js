// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React from 'react';

export const CARD_DEFINITIONS = {
  header: item => item.Name,
  sections: [
    {
      id: 'Name',
      header: 'Name',
      content: item => item.Name
    },
    {
      id: 'InstanceId',
      header: 'Instance Id',
      content: item => item.InstanceId
    },
    {
      id: 'InstanceType',
      header: 'InstanceType',
      content: item => item.InstanceType
    },
    {
      id: 'Region',
      header: 'Region',
      content: item => item.Region
    },
    {
      id: 'State',
      header: 'State',
      content: item => item.State.Name
    }
  ]
};
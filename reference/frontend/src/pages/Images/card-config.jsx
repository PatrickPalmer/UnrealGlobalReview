// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React from 'react';

export const CARD_DEFINITIONS = {
  header: item => item.Name,
  sections: [
    {
      id: 'name',
      header: 'AMI Name',
      content: item => item.Name,
    },
    {
      id: 'ami',
      header: 'AMI ID',
      content: item => item.id,
    },
    {
      id: 'installDir',
      content: item => item.UnrealInstallDir,
      header: 'Unreal Install Dir',
    },
    {
      id: 'description',
      content: item => item.Description,
      header: 'Description',
    },
    {
      id: 'active',
      content: item => item.Active ? "True" : "False",
      header: 'Active',
    }
  ]
};


// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React from 'react';
import { formatIso8601 } from '../../common/format';

export const CARD_DEFINITIONS = {
  header: item => item.DestinationRegion,
  sections:[
    {
      id: 'Ami',
      header: 'Staged AMI',
      content: item => item.Ami,
    },
    {
      id: 'SourceAmi',
      header: 'Source AMI',
      content: item => item.SourceAmi,
    },
    {
      id: 'DestinationRegion',
      header: 'Destination Region',
      content: item => item.DestinationRegion,
    },
    {
      id: 'CreateTime',
      header: 'Date',
      content: item => formatIso8601(item.CreateTime),
    }
  ]
};

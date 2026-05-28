// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React from 'react';
import { NavLink } from 'react-router-dom';

export const CARD_DEFINITIONS = {
  header: item => (
    <NavLink to={"/sessions/" + item.id} fontSize="heading-m">
      {item.id}
    </NavLink>
  ),
  sections: [
    {
      id: 'id',
      header: 'Session ID',
      content: item => item.id,
    },
    {
      id: 'name',
      header: 'Name',
      content: item => item.Name,
    },
    {
      id: 'description',
      content: item => item.Description,
      header: 'Description',
    },
    {
      id: 'region',
      content: item => item.Region,
      header: 'Region',
    },
    {
      id: 'startTime',
      content: item => item.StartTimeFormatted,
      header: 'Start Time',
    },
    {
      id: 'duration',
      content: item => item.Duration,
      header: 'Duration',
    }
  ]
}


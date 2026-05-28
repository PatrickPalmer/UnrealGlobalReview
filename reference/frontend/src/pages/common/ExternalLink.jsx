// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import React from 'react';
import Link, { LinkProps } from '@cloudscape-design/components/link';

function ExternalLink(props) {
  return <Link href="#" external={true} externalIconAriaLabel="Opens in a new tab" {...props} />;
};

export default ExternalLink;
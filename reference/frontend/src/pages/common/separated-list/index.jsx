// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React from 'react';
import styles from './styles-module.scss';

// interface SeparatedListProps {
//   ariaLabel?: string;
//   ariaLabelledBy?: string;
//   items: Array<React.ReactNode>;
// }

function SeparatedList({ ariaLabel, ariaLabelledBy, items }) {
  return (
    <ul aria-label={ariaLabel} aria-labelledby={ariaLabelledBy} className={styles.root}>
      {items.map((item, index) => (
        <li key={index}>{item}</li>
      ))}
    </ul>
  )
};

export default SeparatedList;
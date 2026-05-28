// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React from 'react';
import { StatusIndicator, } from '@cloudscape-design/components';


function ProcessStatusIndicator({status}) {
  if (status === "TERMINATED") {
    return <StatusIndicator>Terminated</StatusIndicator>;
  }
  else if (status === "STOPPED") {
    return <StatusIndicator>Stopped</StatusIndicator>;
  }
  else if (status === "STARTING") {
    return (<StatusIndicator type="in-progress"> Starting </StatusIndicator>);
  }
  else if (status === "RUNNING") {
    return (<StatusIndicator type="in-progress"> Running </StatusIndicator>);
  }
  else if (status === "FAILED") {
    return (<StatusIndicator type="error"> Failed </StatusIndicator>);
  }
  else if (status === "TIMED_OUT") {
    return (<StatusIndicator type="warning"> Timed Out </StatusIndicator>);
  }
  else if (status === "ABORTED") {
    return (<StatusIndicator type="warning"> Aborted </StatusIndicator>);
  }
  else if (status === "MISSING") {
    return (<StatusIndicator type="warning"> Not Available </StatusIndicator>);
  }
  else {
    return (<StatusIndicator type="warning"> Unknown </StatusIndicator>);
  }
}

export default ProcessStatusIndicator;
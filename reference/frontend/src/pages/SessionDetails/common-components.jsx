// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import {
  BreadcrumbGroup,
  Button,
  Header,
  SpaceBetween,
  Spinner,
} from '@cloudscape-design/components';
import { Auth } from 'aws-amplify';
import axiosInstance from '../../common/AxiosComm';
import { v4 as uuid4 } from 'uuid';


export const Breadcrumbs = ({sessionId}) => {

  const navigate = useNavigate();
  const items = [
    {
      text: 'Global Review',
      href: '/sessions',
    },
    {
      text: sessionId,
      href: '/sessions/' + sessionId,
    },
  ];

  const onBreadcrumbClick = event => {
    event.preventDefault();
    console.log('Breadcrumb nav to ' + event.detail.href)
    navigate(event.detail.href);
  };

  return (
    <BreadcrumbGroup 
      items={items} 
      expandAriaLabel="Show path" 
      onClick={onBreadcrumbClick}
      ariaLabel="Breadcrumbs" />
  );
}

export const PageHeader = ({ session, status, notifyFn }) => {

  const sessionID = session['Id'];
  const url = 'https://' + session['SessionUrl'];
  const [terminating, setTerminating] = useState(false);
  
  const terminateSession = e => {
    e.preventDefault();
    console.log("Terminating session: " + sessionID);

    const path = '/sessions/' + sessionID + '/termination';
   
    setTerminating(true);
    axiosInstance.put(path)
      .then(response => {
        if (response && response.data) {
          console.log(response.data);
          if (response.data.success == false) {
            notifyFn("error", "Error terminating session: " + sessionID + ".");
          } else {
            notifyFn("info", "Terminating session: " + sessionID + ".");
          }
        }
        setTerminating(false);
      })
      .catch(error => {
        setTerminating(false);
        console.log(error);
        notifyFn("error", "Error terminating session.");
      });
  };

  const onLogoutClick = event => {
    event.preventDefault();
    Auth.signOut();
  };

  return (
    <Header
      variant="h1"
      actions={
        <SpaceBetween direction="horizontal" size="xs">
          <Button 
            disabled={!session["SessionUrl"] || status !== "RUNNING"} 
            href={url}
            target="_blank">
            Connect
          </Button>
          <Button 
            disabled={status !== "RUNNING"} 
            onClick={terminateSession}>
            {terminating ? <Spinner/> : ''}
            Terminate
          </Button>
          <Button 
            data-testid="header-btn-logout" 
            onClick={onLogoutClick}>
            Logout
          </Button>
        </SpaceBetween>
      }
    >
    </Header>
  );
};

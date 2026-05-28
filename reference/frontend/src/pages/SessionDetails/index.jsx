// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { AppLayout, ContentLayout, SpaceBetween } from '@cloudscape-design/components';
import { Breadcrumbs, PageHeader } from './common-components';
import LogTable from './LogTable';
import SessionSummary from './SessionSummary';
import Notifications from '../../components/Notifications';
import { v4 as uuid4 } from 'uuid';
import '../../styles/base.scss';
import SideNavigation from '@cloudscape-design/components/side-navigation';
import axiosInstance from '../../common/AxiosComm';
import { useNavigate } from 'react-router-dom';

const navItems = [
  { type: 'link', text: 'Sessions', href: '/sessions' },
  { type: 'link', text: 'Images', href: '/images' },
  { type: 'link', text: 'Instances', href: '/instances' },
  { type: 'link', text: 'Stages', href: '/stages' }
];

const SessionDetails = () => {

  const navigate = useNavigate();

  const {sessionId} = useParams();
  const [loading, setLoading] = useState(true);
  const [refreshKey, setRefreshKey] = useState(0);
  const [session, setSession] = useState({});
  const [status, setStatus] = useState('UNKNOWN');

  const onRefreshClick = () => {
    setRefreshKey(oldKey => oldKey + 1);
  };

  useEffect(() => {   
    setLoading(true);
    axiosInstance.get("/sessions/" + sessionId)
      .then(response => {
        if (response && response.data) {
          console.log('Session:')
          console.log(response.data['session'])
          setSession(response.data['session']);
          
          axiosInstance.get("/sessions/" + sessionId + "/status")
            .then(response => {
              if (response && response.data) {
                console.log(response.data['status'])
                setStatus(response.data['status']);
              }
              setLoading(false);
            })
        }
      })
      .catch(error => {
        console.log(error);
        // notifyFn("error", "Error getting the session information.");
        setLoading(false);
      });
  }, [refreshKey, sessionId]);

  // notifications
  const [notices, setNotices] = useState([]);
  const notify = (level, msg) => {
    setNotices([...notices, {id: uuid4(), level:level, msg:msg}]);
  };
  const notified = (id) => {
    setNotices(notices.filter(item => item.id !== id))
  };

  const onSideFollow = e => {
    e.preventDefault();
    navigate(e.detail.href);
  };

  return (
    <AppLayout
      content={
        <ContentLayout header={ <PageHeader session={session} status={status} notifyFn={notify}/> } >
          <SpaceBetween size="l">
            <SessionSummary 
              session={session} 
              status={status} 
              onRefreshClick={onRefreshClick}
              loading={loading}/>
            <LogTable sessionId={sessionId} notifyFn={notify}/>
          </SpaceBetween>
        </ContentLayout>
      }
      headerSelector="#header"
      breadcrumbs={<Breadcrumbs sessionId={sessionId}/>}
      navigationHide={false}
      navigation={
        <SideNavigation 
          header={{ href: '/sessions', text: 'Global Review' }} 
          activeHref="/sessions"
          onFollow={onSideFollow}  
          items={navItems} />}
      toolsHide={true}
      contentType="default"
      notifications={<Notifications notices={notices} notifiedFn={notified}/>}
    />
  );
}

export default SessionDetails;



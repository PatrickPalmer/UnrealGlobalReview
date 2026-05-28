// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React, { useState, useEffect, useRef } from 'react';
import { useCollection } from '@cloudscape-design/collection-hooks';
import { CARD_DEFINITIONS } from './card-config';
import { Pagination, TextFilter, Checkbox, Cards } from '@cloudscape-design/components';
import { Breadcrumbs, ToolsContent, FullPageHeader } from './common-components';
import { BreadcrumbGroup, Button, HelpPanel, SpaceBetween } from '@cloudscape-design/components';
import {
  CustomAppLayout,
  TableEmptyState,
  TableNoMatchState,
} from '../common/common-components';
import Notifications from '../../components/Notifications';
import { paginationLabels } from '../../common/labels';
import { getFilterCounterText } from '../../common/tableCounterStrings';
import axiosInstance from '../../common/AxiosComm';
import { v4 as uuid4 } from 'uuid';
import '../../styles/base.scss';
import SideNavigation from '@cloudscape-design/components/side-navigation';
import { formatIsoDuration, formatIso8601 } from '../../common/format';
import { useNavigate } from 'react-router-dom';

const PageSize = 20;

const navItems = [
  { type: 'link', text: 'Sessions', href: '/sessions' },
  { type: 'link', text: 'Images', href: '/images' },
  { type: 'link', text: 'Instances', href: '/instances' },
  { type: 'link', text: 'Stages', href: '/stages' }
];


function CardContent({ loadHelpPanelContent, changeCallback, notifyFn }) {
  
  const [checked, setChecked] = React.useState(false);
  const [loading, setLoading] = useState(true);
  const [sessions, setSessions] = useState([]);

  function formatContent(item) {
    item.id = item.Id;

    item.Duration = formatIsoDuration(item.Duration);

    // format description
    let desc = item.Description; 
    if (desc == '') {
      desc = 'Global Review Session';
      item.Description = desc;
    }

    // format start time
    item.StartTimeFormatted = formatIso8601(item.StartTime);

    return item;
  };

  useEffect(() => { 
    setLoading(true);
    axiosInstance.get("/sessions" + (checked ? "?all=1" : ""))
      .then(response => {
        if (response && response.data) {
          console.log(response.data);
          setSessions(response.data['session'].map(formatContent));
        }
        setLoading(false);
      })
      .catch(error => {
        console.log(error);
        notifyFn("error", "Error getting the session list.");
      });
  }, [checked]);

  const { items, actions, filteredItemsCount, collectionProps, filterProps, paginationProps } = useCollection(
    sessions,
    {
      filtering: {
        empty: <TableEmptyState resourceName="Session" />,
        noMatch: <TableNoMatchState onClearFilter={() => actions.setFiltering('')} />,
      },
      pagination: { pageSize: 20 },
      sorting: { defaultState: { sortingColumn: CARD_DEFINITIONS.sections[0] } },
      selection: {},
    }
  );

  return (
    <Cards
      {...collectionProps}
      cardDefinition={CARD_DEFINITIONS}
      visibleSections={['name', 'region', 'startTime', 'description', 'duration']} 
      cardsPerRow={[
        { cards: 1 },
        { minWidth: 500, cards: 2 }
      ]}
      loading={loading}
      loadingText="Loading Sessions"
      items={items}
      header={
        <FullPageHeader
          selectedItems={collectionProps.selectedItems}
          totalItems={sessions}
          items={sessions}
          loadHelpPanelContent={loadHelpPanelContent}
        />
      }
      filter={
        <div>
          <TextFilter
            {...filterProps}
            filteringAriaLabel="Filter sessions"
            filteringPlaceholder="Find sessions"
            countText={getFilterCounterText(filteredItemsCount)}
          />
          <br></br>
          <Checkbox
            onChange={({ detail }) =>
              setChecked(detail.checked)
            }
            checked={checked}
          >
            All Sessions
          </Checkbox>
        </div>
      }
      pagination={<Pagination {...paginationProps} ariaLabels={paginationLabels} />}
    />
  );
}

const Sessions = ( sessions, loading ) => {
  const navigate = useNavigate();

  const [toolsOpen, setToolsOpen] = useState(false);
  const appLayout = useRef();

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
    <CustomAppLayout
      ref={appLayout}
      navigationHide={false}
      navigation={
        <SideNavigation 
          header={{ href: '/sessions', text: 'Global Review' }} 
          activeHref="/sessions"
          onFollow={onSideFollow} 
          items={navItems} />}
      notifications={<Notifications notices={notices} notifiedFn={notified}/>}
      breadcrumbs={<Breadcrumbs sessions={sessions}/>}
      content={
        <CardContent
          sessions={sessions}
          loading={loading}
          loadHelpPanelContent={() => {
            setToolsOpen(true);
            appLayout.current?.focusToolsClose();
          }}
          notifyFn={notify}
        />
      }
      tools={<ToolsContent />}
      toolsOpen={toolsOpen}
      onToolsChange={({ detail }) => setToolsOpen(detail.open)}
      stickyNotifications
    />
  );
}

export default Sessions;

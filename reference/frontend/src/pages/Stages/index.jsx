// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React, {useState, useEffect, useRef} from 'react';
import { useParams } from 'react-router-dom';
import { CARD_DEFINITIONS } from './card-config';
import { useCollection } from '@cloudscape-design/collection-hooks';
import { Pagination, Cards, TextFilter } from '@cloudscape-design/components';
import { Breadcrumbs, ToolsContent, FullPageHeader } from './common-components';
import {
  CustomAppLayout,
  TableEmptyState,
  TableNoMatchState,
} from '../common/common-components';
import Notifications from '../../components/Notifications';
import { paginationLabels } from '../../common/labels';
import { getFilterCounterText } from '../../common/tableCounterStrings';
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

function CardContent({ stages, loading, loadHelpPanelContent, changeCallback, notifyFn }) {
  
  const { items, actions, filteredItemsCount, collectionProps, filterProps, paginationProps } = useCollection(
    stages,
    {
      filtering: {
        empty: <TableEmptyState resourceName="Stage" />,
        noMatch: <TableNoMatchState onClearFilter={() => actions.setFiltering('')} />,
      },
      pagination: { pageSize: 20 },
      sorting: { defaultState: { sortingColumn: CARD_DEFINITIONS.sections[0] } },
      selection: {},
    }
  );
  
  return (
    <div>
    <Cards
      {...collectionProps}
      cardDefinition={CARD_DEFINITIONS}
      visibleSections={['Ami', 'SourceAmi', 'DestinationRegion', 'CreateTime']} 
      loading={loading}
      loadingText="Loading Stages"
      items={items}
      cardsPerRow={[
        { cards: 1 },
        { minWidth: 500, cards: 2 }
      ]}
      variant="full-page"
      header={
        <FullPageHeader
          selectedItems={collectionProps.selectedItems}
          totalItems={stages}
          stages={stages}
          loadHelpPanelContent={loadHelpPanelContent}
        />
      }
      filter={
        <TextFilter
          {...filterProps}
          filteringAriaLabel="Filter stages"
          filteringPlaceholder="Find stages"
          countText={getFilterCounterText(filteredItemsCount)}
        />
      }
      pagination={<Pagination {...paginationProps} ariaLabels={paginationLabels} />}
    />
    </div>
  );
}


const Stages = () => {
  const {stage} = useParams();
  const navigate = useNavigate();

  const [toolsOpen, setToolsOpen] = useState(false);
  const appLayout = useRef();

  const [loading, setLoading] = useState(true);
  const [stages, setStages] = useState([]);
  const [refreshKey, setRefreshKey] = useState(0);
  const [notices, setNotices] = useState([]);

  const notify = (level, msg) => {
    setNotices([...notices, {id: uuid4(), level:level, msg:msg}]);
  };
  const notified = (id) => {
    setNotices(notices.filter(item => item.id !== id))
  };

  useEffect(() => { 
    setLoading(true);
    axiosInstance.get("/stages")
      .then((response) => {
        if (response && response){
          console.log('Response', response);
          setStages(response.data['stage'].map(x => {return {...x, id: x.Ami + x.DestinationRegion}}));
        }
        setLoading(false);
      })
      .catch(error => {
        console.log(error);
        notify("error", "Error getting the stages list.");
      });
  }, [refreshKey]);

  const onChangeCallback = () => {
    setRefreshKey(oldKey => oldKey + 1);
  };

  const onSideFollow = e => {
    e.preventDefault();
    navigate(e.detail.href);
  };

  return (
     <CustomAppLayout
      ref={appLayout}
      navigationHide={false}
      navigation={<SideNavigation 
        header={{ href: '/stages', text: 'Global Review' }} 
        activeHref="/stages" 
        onFollow={onSideFollow} 
        items={navItems} />}
      notifications={<Notifications notices={notices} notifiedFn={notified}/>}
      breadcrumbs={<Breadcrumbs stages={stages}/>}
      content={
        <CardContent
          stages={stages}
          loading={loading}
          loadHelpPanelContent={() => {
            setToolsOpen(true);
            appLayout.current?.focusToolsClose();
          }}
          changeCallback={onChangeCallback}
          notifyFn={notify}
        />
      }
      contentType="table"
      tools={<ToolsContent />}
      toolsOpen={toolsOpen}
      onToolsChange={({ detail }) => setToolsOpen(detail.open)}
      stickyNotifications
    />
  );
}

export default Stages ;



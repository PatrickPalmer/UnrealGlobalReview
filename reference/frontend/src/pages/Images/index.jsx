// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { useCollection } from '@cloudscape-design/collection-hooks';
import { CARD_DEFINITIONS } from './card-config';
import { Pagination, Cards, TextFilter } from '@cloudscape-design/components';
import { Breadcrumbs, ToolsContent, FullPageHeader } from './common-components';
import {
  CustomAppLayout,
  TableEmptyState,
  TableNoMatchState,
} from '../common/common-components';
import Notifications from '../../components/Notifications';
import RegisterImageModal from './RegisterImageModal';
import { paginationLabels } from '../../common/labels';
import { getFilterCounterText } from '../../common/tableCounterStrings';
import { v4 as uuid4 } from 'uuid';
import '../../styles/base.scss';
import SideNavigation from '@cloudscape-design/components/side-navigation';
import { useNavigate } from 'react-router-dom';
import { useQuery } from "@tanstack/react-query";
import { getImages, 
         ImagesCacheName } from '../../data/Images';

const navItems = [
  { type: 'link', text: 'Sessions', href: '/sessions' },
  { type: 'link', text: 'Images', href: '/images' },
  { type: 'link', text: 'Instances', href: '/instances' },
  { type: 'link', text: 'Stages', href: '/stages' }
];

function CardContent({ images, loading, loadHelpPanelContent, changeCallback, notifyFn }) {
  
  const [displayCreateImage, setDisplayCreateImage] = useState(false);

  const { items, actions, filteredItemsCount, collectionProps, filterProps, paginationProps } = useCollection(
    images,
    {
      filtering: {
        empty: <TableEmptyState resourceName="Image" />,
        noMatch: <TableNoMatchState onClearFilter={() => actions.setFiltering('')} />,
      },
      pagination: { pageSize: 20 },
      selection: {},
    }
  );

  const onCreateCallback = () => {
    setDisplayCreateImage(true);
  };

  const onSaveImage = (ami, name) => {
    notifyFn("success", `Successfully added ${name} (${ami})`);
    setDisplayCreateImage(false);
    changeCallback();
  };

  const onCancelCreateImage = () => {
    setDisplayCreateImage(false);
  };

  const onCreateImageError = msg => {
    notifyFn("error", msg);
    setDisplayCreateImage(false);
  };

  return (
    <div>
    <RegisterImageModal
      visible={displayCreateImage}
      url={"/images/"}
      onCancel={onCancelCreateImage}
      onSave={onSaveImage}
      onError={onCreateImageError}
      notifyFn={notifyFn}
    />
    <Cards
      {...collectionProps}
      cardDefinition={CARD_DEFINITIONS}
      visibleSections={['ami', 'name', 'installDir', 'active', 'description']}
      loading={loading}
      loadingText="Loading Images"
      items={items}
      variant="full-page"
      cardsPerRow={[
        { cards: 1 },
        { minWidth: 500, cards: 2 }
      ]}
      header={
        <FullPageHeader
          selectedItems={collectionProps.selectedItems}
          totalItems={images}
          images={images}
          loadHelpPanelContent={loadHelpPanelContent}
          onCreateCallback={onCreateCallback}
        />
      }
      filter={
        <TextFilter
          {...filterProps}
          filteringAriaLabel="Filter images"
          filteringPlaceholder="Find images"
          countText={getFilterCounterText(filteredItemsCount)}
        />
      }
      pagination={<Pagination {...paginationProps} ariaLabels={paginationLabels} />}
    />
    </div>
  );
}

const Images = () => {

  const navigate = useNavigate();
  const {image} = useParams();

  const [toolsOpen, setToolsOpen] = useState(false);
  const appLayout = useRef();

  const [refreshKey, setRefreshKey] = useState(0);

  // notifications
  const [notices, setNotices] = useState([]);
  const notify = (level, msg) => {
    setNotices([...notices, {id: uuid4(), level:level, msg:msg}]);
  };
  const notified = (id) => {
    setNotices(notices.filter(item => item.id !== id))
  };

  let images = [];
  const { data: srcImages, errorImages, isLoadingImages } = useQuery({
    queryKey: [ImagesCacheName], 
    queryFn: getImages});
  if (errorImages) {
    notify("error", "Error retrieving the AMI Image list.");
  } else if (!isLoadingImages && srcImages) {
    images = srcImages.map(x => {return {...x, id: x.Ami}});
  }

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
      navigation={
        <SideNavigation 
          header={{ href: '/sessions', text: 'Global Review' }} 
          activeHref="/images"
          onFollow={onSideFollow}  
          items={navItems} />}
      notifications={<Notifications notices={notices} notifiedFn={notified}/>}
      breadcrumbs={<Breadcrumbs images={images}/>}
      content={
        <CardContent
          images={images}          
          loading={isLoadingImages}
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

export default Images;

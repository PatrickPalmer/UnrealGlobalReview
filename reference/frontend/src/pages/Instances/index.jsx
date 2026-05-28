// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React, {useState, useEffect, useRef} from 'react';
import { useParams } from 'react-router-dom';
import { CARD_DEFINITIONS } from './card-config';
import { useCollection } from '@cloudscape-design/collection-hooks';
import { Pagination, Cards, TextFilter, Checkbox } from '@cloudscape-design/components';
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
import TerminateInstanceModal from './TerminateInstanceModal';

const navItems = [
  { type: 'link', text: 'Sessions', href: '/sessions' },
  { type: 'link', text: 'Images', href: '/images' },
  { type: 'link', text: 'Instances', href: '/instances' },
  { type: 'link', text: 'Stages', href: '/stages' }
];


function ProcessInstances(instances, region) {
  return instances
    // filter out terminated instances
    .filter(inst => inst.State.Name !== "terminated" && inst.State.Name !== "shutting-down")
    // get the instance name from tags and add in region
    .map(inst => {
      let name = "";
      for (let i = 0; i < inst.Tags.length; i += 1) {
        if (inst.Tags[i].Key == 'Name') {
          name = inst.Tags[i].Value;
        }
      }
      return {...inst, 'Region': region, 'Name': name}
    });
}


function CardContent({ instances, loading, loadHelpPanelContent, changeCallback, notifyFn, showAll, setShowAll }) {

  const [displayTerminateInstance, setDisplayTerminateInstance] = useState(false);
  
  const { items, actions, filteredItemsCount, collectionProps, filterProps, paginationProps } = useCollection(
    instances,
    {
      filtering: {
        empty: <TableEmptyState resourceName="Instance" />,
        noMatch: <TableNoMatchState onClearFilter={() => actions.setFiltering('')} />,
      },
      pagination: { pageSize: 20 },
      sorting: { defaultState: { sortingColumn: CARD_DEFINITIONS.sections[0] } },
      selection: {},
    }
  );

  const onTerminateCallback = () => {
    setDisplayTerminateInstance(true);
  };

  const onTerminateInstance = (results) => {
    const parts = results.upload.split('/');
    notifyFn("success", `Successfully uploaded ${parts[parts.length-1]} as id ${parts[parts.length-2]}`);
    setDisplayTerminateInstance(false);
    changeCallback();
  };

  const onCancelTerminateInstance = () => {
    setDisplayTerminateInstance(false);
  };

  const onTerminateInstanceError = msg => {
    notifyFn("error", msg);
    setDisplayTerminateInstance(false);
  };

  return (
    <div>
      <TerminateInstanceModal
        visible={displayTerminateInstance}
        items={collectionProps.selectedItems}
        onCancel={onCancelTerminateInstance}
        onSave={onTerminateInstance}
        onError={onTerminateInstanceError}
      />
      <Cards
        {...collectionProps}
        cardDefinition={CARD_DEFINITIONS}
        visibleColumns={['Name', 'InstanceId', 'InstanceType', "Region", "State"]}
        cardsPerRow={[
          { cards: 1 },
          { minWidth: 500, cards: 2 }
        ]}
        loading={loading}
        loadingText="Loading Instances"
        items={items}
        selectionType="single"
        header={
          <FullPageHeader
            selectedItems={collectionProps.selectedItems}
            totalItems={instances}
            instances={instances}
            loadHelpPanelContent={loadHelpPanelContent}
            terminateEnabled={collectionProps.selectedItems.length > 0}
            onTerminateCallback={onTerminateCallback}
          />
        }
        filter={
          <div>
            <TextFilter
              {...filterProps}
              filteringAriaLabel="Filter instances"
              filteringPlaceholder="Find instances"
              countText={getFilterCounterText(filteredItemsCount)}
            />
            <br></br>
            <Checkbox
              onChange={({ detail }) =>
                setShowAll(detail.checked)
              }
              checked={showAll}
            >
            All Instances
          </Checkbox>
        </div>
        }
        pagination={<Pagination {...paginationProps} ariaLabels={paginationLabels} />}
      />
    </div>
  );
}


const Instances = () => {
  const {instance} = useParams();
  const navigate = useNavigate();

  const [toolsOpen, setToolsOpen] = useState(false);
  const appLayout = useRef();

  const [showAll, setShowAll] = useState(false);
  const [loading, setLoading] = useState(true);
  const [regions, setRegions] = useState([]);
  const [instances, setInstances] = useState([]);
  const [refreshKey, setRefreshKey] = useState(0);

  const [notices, setNotices] = useState([]);
  const notify = (level, msg) => {
    setNotices([...notices, {id: uuid4(), level:level, msg:msg}]);
  };
  const notified = (id) => {
    setNotices(notices.filter(item => item.id !== id))
  };

  const onCheckedChangeCallback = (checked) => {
    setShowAll(checked);
    setRefreshKey(oldKey => oldKey + 1);
  };

  useEffect(() => { 
    setLoading(true);
    Promise.all([
        axiosInstance.get("/config/regions/installed"),
        axiosInstance.get("/stages")
      ])
      .then((responses) => {
        let stages = responses[1].data['stage'].map(x => {return x.DestinationRegion});

        // make sure the list of region names is unique
        setRegions(Array.from(new Set([responses[0].data['region'], ...stages])));

        setLoading(false);
      })
      .catch(error => {
        setLoading(false);
        console.log(error);
        notify("error", "Error getting the stages list.");
      });
  }, [refreshKey]);

  useEffect(() => { 
    if (regions.length == 0)
    {
      setInstances([]);
      return;
    }

    setLoading(true);
    let promises = regions.map(r => {
      return axiosInstance.get("/instances/" + r  + (showAll ? "?all=1" : ""))
    });

    Promise.all(promises)
      .then((response) => {
        let all_instances = [];
        response.map((r, index) => {
          console.log("get_instances response for region " + regions[index]);
          console.log(r.data['instance']);
          all_instances = [...all_instances, ...ProcessInstances(r.data['instance'], regions[index])];
        });
        setInstances(all_instances);
        setLoading(false);
      })
      .catch(error => {
        setLoading(false);
        console.log(error);
        notify("error", "Error getting the instances list.");
      });

  }, [regions]);

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
        header={{ href: '/instances', text: 'Global Review' }} 
        activeHref="/instances"
        onFollow={onSideFollow}  
        items={navItems} />}
      notifications={<Notifications notices={notices} notifiedFn={notified}/>}
      breadcrumbs={<Breadcrumbs instances={instances}/>}
      content={
        <CardContent
          instances={instances}
          loading={loading}
          loadHelpPanelContent={() => {
            setToolsOpen(true);
            appLayout.current?.focusToolsClose();
          }}
          changeCallback={onChangeCallback}
          notifyFn={notify}
          showAll={showAll}
          setShowAll={onCheckedChangeCallback}
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

export default Instances ;




// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Header,
  FormField,
  SpaceBetween,
  Select,
  Input,
  Spinner,
  Button
} from '@cloudscape-design/components';
import axiosInstance from "../../../common/AxiosComm";
import { getFieldOnChange } from '../utils';
import { DEFAULT_STEP_INFO } from '../steps-config';

const formatStreamOptions = (streams, notifyFn) => {
  let streamsList = [];
  for (let i = 0; i < streams.length; i++) {
    streamsList.push({
      label: streams[i].Name,
      value: streams[i].Stream
    });
  }
  return streamsList;
};

const formatUMapOptions = (umaps, notifyFn) => {
  let uMapList = [];
  for (let i = 0; i < umaps.length; i++) {
    uMapList.push({
      label: umaps[i].depotFile,
      value: umaps[i].depotFile
    });
  }
  if (uMapList.length == 0) {
    notifyFn("warn", "No Maps found in the Perforce Helix Stream.");
  }
  return uMapList;
};

const formatUProjectOptions = (uprojects, notifyFn) => {
  let uProjectList = [];
  for (let i = 0; i < uprojects.length; i++) {
    uProjectList.push({
      label: uprojects[i].depotFile,
      value: uprojects[i].depotFile
    });
  }
  return uProjectList;
};


const PerforceConnect = ({ 
  port,
  username,
  password,
  onChange, 
  notifyFn,
  streams,
  setStreams
}) => {
  const [loading, setLoading] = useState(false);
  const onPortChange = getFieldOnChange('input', 'port', onChange);
  const onUsernameChange = getFieldOnChange('input', 'username', onChange);
  const onPasswordChange = getFieldOnChange('input', 'password', onChange);

  const getStreams = e => {
    e.preventDefault();
    console.log("Getting list of streams.");
    setLoading(true);
    setStreams({streams: [], projects: [], levels: [], streams_state: "loading", projects_state: "pending"})
    onChange({
      'stream': '',
      'uproject': '',
      'umap': ''
    });

    axiosInstance.post('/p4/streams', {
      Port: port,  
      User: username,
      Password: password
    })
    .then(function (response) {
      setLoading(false);
      setStreams({streams: formatStreamOptions(response.data['streams'], notifyFn), projects: [], levels:[], streams_state: "finished", projects_state: "pending"});
    })
    .catch(error => {
      notifyFn("error", "Invalid credentials. Unable to connect to Perforce Helix.");
      setLoading(false);
      setStreams({streams: [], projects: [], levels:[], streams_state: "error", projects_state: "pending"});
      console.log(error);
    });
  };

  return (
    <Container
      header={<Header variant="h2">Connect to Perforce Helix</Header>}
    >
      <SpaceBetween size="l">
        <FormField
          label="Perforce Helix Port"
          errorText={
            port === null && 'Perforce Helix port is required.'
          }
          i18nStrings={{
            errorIconAriaLabel: 'Error',
          }}
        >
          <Input
            value={port}
            placeholder="ssl:[IP Address]:1666"
            onChange={onPortChange}
          />
        </FormField>
        <FormField
          label="Perforce Helix user name"
          errorText={
            username === null && 'Perforce Helix user name is required.'
          }
          i18nStrings={{
            errorIconAriaLabel: 'Error',
          }}
        >
          <Input
            value={username}
            placeholder="enter user name"
            onChange={onUsernameChange}
          />
        </FormField>
        <FormField
            label="Perforce Helix password"
            errorText={
              password === null && 'Perforce Helix password is required.'
            }
            i18nStrings={{
              errorIconAriaLabel: 'Error',
            }}
          >
            <Input
              value={password}
              type="password"
              placeholder="enter password"
              onChange={onPasswordChange}
            />
        </FormField>
        <Button onClick={getStreams} variant="primary">
          {loading && <Spinner/>}
          Get Streams
        </Button>
      </SpaceBetween>      
    </Container>
  );
};

const StreamsList = ({ 
  stream,
  port,
  username,
  password,
  onChange,
  notifyFn,
  streams,
  setStreams 
}) => {
  const [loading, setLoading] = useState(false);
  const onStreamChange = getFieldOnChange('select', 'stream', onChange);

  let path = '';
  if (stream) {
    path = '/p4/streams/' + stream.value;
  }

  const getUnrealMaps = e => {
    e.preventDefault();
    console.log("Getting list of Unreal Engine maps.");

    if (!stream) {
      return;
    }

    // loading two lists
    setStreams({...streams, projects: [], levels: [], projects_state: "loading"})
    onChange({
      'uproject': '',
      'umap': ''
    });
    setLoading(true);

    Promise.all([

      axiosInstance.post(path + '/umaps', {
        Port: port,  
        User: username,
        Password: password
      }),

      axiosInstance.post(path + '/uprojects', {
        Port: port,  
        User: username,
        Password: password
      })
    ])
    .then(function (response) {
      setLoading(false);
      setStreams({...streams, 
                  levels: formatUMapOptions(response[0].data['umap'], notifyFn),
                  projects: formatUProjectOptions(response[1].data['uproject'], notifyFn),
                  projects_state: "finished"});
    })
    .catch(error => {
      setLoading(false);
      setStreams({...streams, projects: [], levels: [], projects_state: "error"});
      console.log(error);
    });
  };

  return (
    <div id="streamContainer">
      <Container
        header={<Header variant="h2">Perforce Helix Streams</Header>}
      >
        <SpaceBetween size="l">
          <FormField
            description="List of streams on the Perforce Helix server."
            errorText={
              stream === null && 'Stream is required.'
            }
            i18nStrings={{
              errorIconAriaLabel: 'Error',
            }}
          >
            <Select
              selectedOption={stream}
              onChange={onStreamChange}
              options={streams.streams}
              disabled={streams.streams_state !== "finished"}
              selectedAriaLabel="Selected"
              placeholder="select stream"
            />
          </FormField>
          <Button onClick={getUnrealMaps} variant="primary" disabled={!streams.streams.length}>
            {loading && <Spinner/>}
            Get Unreal Levels
          </Button>
        </SpaceBetween>      
      </Container>
    </div>
  );
};

const UMapsList = ({ 
  umap,
  uproject,
  onChange,
  streams,
  setStreams
}) => {
  const onUMapChange = getFieldOnChange('select', 'umap', onChange);
  const onUProjectChange = getFieldOnChange('select', 'uproject', onChange);

  return (
    <div id="unrealContainer">
      <Container
        header={<Header variant="h2">Unreal Engine</Header>}
      >
        <SpaceBetween size="l">
          <FormField
            label="Project"
            description="List of Unreal Engine projects on the Perforce Helix server."
            errorText={
              uproject === null && 'Unreal Engine project is required.'
            }
            i18nStrings={{
              errorIconAriaLabel: 'Error',
            }}
          >
            <Select
              options={streams.projects}
              disabled={streams.projects_state !== "finished"}
              onChange={onUProjectChange}
              selectedAriaLabel="Selected"
              selectedOption={uproject}
              placeholder="select project"
            />
          </FormField>
          <FormField
            label="Level"
            description="List of Unreal Engine levels on the Perforce Helix server."
            errorText={
              umap === null && 'UMap is required.'
            }
            i18nStrings={{
              errorIconAriaLabel: 'Error',
            }}
          >
            <Select
              options={streams.levels}
              onChange={onUMapChange}
              selectedAriaLabel="Selected"
              disabled={streams.projects_state !== "finished"}
              selectedOption={umap}
              placeholder="select level"
            />
          </FormField>
        </SpaceBetween>      
      </Container>
    </div>
  );
};

const Step2 = ({ info: { engine }, setHelpPanelContent, onChange, notifyFn, streams, setStreams }) => {
  const childProps = { ...engine, setHelpPanelContent, onChange, notifyFn, streams, setStreams };
  return (
    <Box margin={{ bottom: 'l' }}>
      <SpaceBetween size="l">
        <PerforceConnect {...childProps} />
        <StreamsList {...childProps} />
        <UMapsList {...childProps} />
      </SpaceBetween>
    </Box>
  );
};

export default Step2;
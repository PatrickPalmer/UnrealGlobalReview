// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Input, 
  Header,
  FormField,
  SpaceBetween,
  Select,
  Textarea
} from '@cloudscape-design/components';
import { CLASS_OPTIONS, DURATION_OPTIONS } from '../steps-config';
import { getFieldOnChange } from '../utils';
import { useQuery } from "@tanstack/react-query";
import { getAvailableRegions, 
         AvailableRegionsCacheName,
         processRegionsIntoUxOptions } from '../../../data/AvailableRegions';
import { KeyPairsCacheName,
         getKeyPairs,
         processKeypairIntoUxOptions } from '../../../data/KeyPairs';
import { ImagesCacheName,
         getImages,
         processImagesIntoUxOptions } from '../../../data/Images';


const SessionOptions = ({ 
  sessionName,
  instanceClass, 
  region, 
  ami, 
  duration,  
  description,
  keypair,
  onChange,
  notifyFn 
}) => {
  const onInstanceClassChange = getFieldOnChange('select', 'instanceClass', onChange);
  const onRegionChange = getFieldOnChange('select', 'region', onChange);
  const onAmiChange = getFieldOnChange('select', 'ami', onChange);
  const onDurationChange = getFieldOnChange('select', 'duration', onChange);
  const onDescriptionChange = getFieldOnChange('textarea', 'description', onChange);
  const onKeypairChange = getFieldOnChange('select', 'keypair', onChange);
  const onSessionNameChange = getFieldOnChange('input', 'sessionName', onChange);

  const [loading, setLoading] = useState(true);

  const { data: regions, errorRegions, isLoadingRegions } = useQuery({
    queryKey: [AvailableRegionsCacheName], 
    queryFn: getAvailableRegions});
  if (errorRegions) {
    notifyFn("error", "Error retrieving the Region list.");
  }
  const processedRegions = processRegionsIntoUxOptions(regions);

  const { data: keypairs, errorKeypairs, isLoadingKeypairs } = useQuery({
    queryKey: [KeyPairsCacheName], 
    queryFn: getKeyPairs});
  if (errorKeypairs) {
    notifyFn("error", "Error retrieving the Key Pair list.");
  }
  const processedKeypairs = processKeypairIntoUxOptions(keypairs);

  const { data: images, errorImages, isLoadingImages } = useQuery({
    queryKey: [ImagesCacheName], 
    queryFn: getImages});
  if (errorImages) {
    notifyFn("error", "Error retrieving the AMI Image list.");
  }
  const processedImages = processImagesIntoUxOptions(images);

  return (
    <Container>
      <SpaceBetween size="l">
        <FormField
          label="Name"
          errorText={
            sessionName === null && 'Session name is required.'
          }
          i18nStrings={{
            errorIconAriaLabel: 'Error',
          }}
        >
          <Input
            value={sessionName}
            placeholder="enter session name"
            onChange={onSessionNameChange}
          />
        </FormField>
        <FormField
          label={
            <span>
              Description <i>- optional</i>{" "}
            </span>
          }
        >
          <Textarea 
            value={description}
            onChange={onDescriptionChange}
          />
        </FormField>
        <FormField
          label="Instance Type"
          // info={<InfoLink onFollow={() => setHelpPanelContent(detailsToolsContent.instanceClass)} />}
          description="Instance type allocates the computational, network, and memory capacity required by planned workload of this instance."
          errorText={
            instanceClass === null && 'Instance class is required.'
          }
          i18nStrings={{
            errorIconAriaLabel: 'Error',
          }}
        >
          <Select
            options={CLASS_OPTIONS}
            placeholder='select instance class'
            onChange={onInstanceClassChange}
            selectedAriaLabel="Selected"
            selectedOption={instanceClass}
          />
        </FormField>
        <FormField
          label="AMI"
          description="Registered Amazon Machine Images (AMIs)."
          errorText={
            ami === null && 'AMI is required.'
          }
          i18nStrings={{
            errorIconAriaLabel: 'Error',
          }}
        >
          <Select
            options={processedImages}
            placeholder='select AMI'
            onChange={onAmiChange}
            selectedAriaLabel="Selected"
            selectedOption={ami}
          />
        </FormField>
        <FormField
          label="Region"
          description="AWS Regions that offer G5 and G4dn instances."
          errorText={
            region === null && 'AWS Region is required.'
          }
          i18nStrings={{
            errorIconAriaLabel: 'Error',
          }}
        >
          <Select
            options={processedRegions}
            placeholder='select region'
            onChange={onRegionChange}
            selectedAriaLabel="Selected"
            selectedOption={region}
          />
        </FormField>
        <FormField
          label="Duration"
          description="Session will terminate after this amount of time."
          errorText={
            region === null && 'Duration is required.'
          }
          i18nStrings={{
            errorIconAriaLabel: 'Error',
          }}
        >
          <Select
            options={DURATION_OPTIONS}
            placeholder='select duration'
            onChange={onDurationChange}
            selectedAriaLabel="Selected"
            selectedOption={duration}
          />
        </FormField>
        <FormField
          label={
            <span>
              Key pair <i>- optional</i>{" "}
            </span>
          }
          description="Choose a key pair."
          i18nStrings={{
            errorIconAriaLabel: 'Error',
          }}
        >
          <Select
            options={processedKeypairs}
            placeholder='None'
            onChange={onKeypairChange}
            selectedAriaLabel="Selected"
            selectedOption={keypair}
          />
        </FormField>
      </SpaceBetween>
    </Container>
  );
};

const Step1 = ({ info: { details }, setHelpPanelContent, onChange, notifyFn }) => {
  const childProps = { ...details, setHelpPanelContent, onChange, notifyFn };
  return (
    <Box margin={{ bottom: 'l' }}>
      <SpaceBetween size="l">
        <SessionOptions {...childProps} />
      </SpaceBetween>
    </Box>
  );
};

export default Step1;
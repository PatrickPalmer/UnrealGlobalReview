// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React, { useState, useEffect, useRef } from 'react';
import {
  Button,
  SpaceBetween,
  Modal,
  FormField,
  Form,
  Input,
  Textarea,
} from '@cloudscape-design/components';
import { addImage } from "../../data/Images";


const RegisterImageModal = props => {
  const [ami, setAmi] = React.useState("");
  const [imageName, setImageName] = React.useState("");
  const [description, setDescription] = React.useState("");
  const [installDir, setInstallDir] = React.useState("");

  const addImageFn = addImage();

  const cancelHandler = event => {
    event.preventDefault();
    props.onCancel();
  };

  const onFormSubmit = e => {
    e.preventDefault();
    console.log("Registering Image.");

    addImageFn.mutateAsync({
      Ami: ami,
      Name: imageName,
      Description: description,
      UnrealInstallDir: installDir
    })
    .then(function (response) {
      console.log(response);
      props.onSave(ami, imageName);
    })
    .catch(error => {
      props.onError("Unable to register image.");
      console.log(error);
    });
  };
  
  return (
    <Modal
      onDismiss={cancelHandler}
      visible={props.visible}
      closeAriaLabel="Close modal"
      header="Register Image"
    > 
    <SpaceBetween direction="vertical" size="l">
    <hr
      style={{
        color: 'gray',
        background: 'gray',
        border: 'gray',
        height: '1px',
      }}
    />
    <form onSubmit={onFormSubmit}>
        <Form
          actions={
            <SpaceBetween direction="horizontal" size="xs">
              <Button variant="link" onClick={cancelHandler}>
                Cancel
              </Button>
              <Button formAction="submit" variant="primary">
                Register Image
              </Button>
            </SpaceBetween>
          }
        >
          <SpaceBetween direction="vertical" size="xl">
          <FormField
            label="Name"
            errorText={
                imageName === null && 'Name is required.'
            }
            i18nStrings={{
              errorIconAriaLabel: 'Error',
            }}
          >
            <Input
              value={imageName}
              onChange={event =>
                setImageName(event.detail.value)
              }
            />
          </FormField>
          <FormField
            label="AMI ID"
            errorText={
              ami === null && 'AMI ID is required.'
            }
            i18nStrings={{
              errorIconAriaLabel: 'Error',
            }}
          >
            <Input
              value={ami}
              onChange={event =>
                setAmi(event.detail.value)
              }
            />
          </FormField>
          <FormField
            label="Unreal Installation Directory"
            errorText={
              installDir === null && 'Unreal Installation Directory is required.'
            }
            i18nStrings={{
              errorIconAriaLabel: 'Error',
            }}
          >
            <Input
              value={installDir}
              onChange={event =>
                setInstallDir(event.detail.value)
              }
              placeholder = "i.e., C:/UE_5.3"
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
            onChange={event =>
              setDescription(event.detail.value)
            }
          />
          </FormField>
          </SpaceBetween>
        </Form>
      </form>
      </SpaceBetween>
    </Modal>
  );
};

export default RegisterImageModal;

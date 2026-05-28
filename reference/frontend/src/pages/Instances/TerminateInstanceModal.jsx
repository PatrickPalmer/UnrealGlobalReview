// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React from 'react';
import {
  Button,
  SpaceBetween,
  Modal,
  Form,
} from '@cloudscape-design/components';
import axiosInstance from "../../common/AxiosComm";


const TerminateInstanceModal = props => {
  const [ami, setAmi] = React.useState("");
  const [imageName, setImageName] = React.useState("");

  const cancelHandler = event => {
    event.preventDefault();
    props.onCancel();
  };

  const onError = () => {
    props.onError("Unable to terminate instance.");
  };

  const onFormSubmit = e => {
    e.preventDefault();

    let url = "/instances/" + props.items[0].Region + "/" + props.items[0].InstanceId + "/termination";
    axiosInstance.put(url, {})
    .then(function (response) {
      console.log(response);
      window.location.reload(true);
    })
    .catch(error => {
      onError(error);
      console.log(error);
    });
  };
  
  return (
    <Modal
      onDismiss={cancelHandler}
      visible={props.visible}
      closeAriaLabel="Close modal"
      header="Terminate Instance?"
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
                Terminate
              </Button>
            </SpaceBetween>
          }
        >
          <SpaceBetween direction="vertical" size="xl">
            <div>
            To confirm that you want to terminate the instances, choose the terminate button below. Instances with termination protection enabled will not be terminated. Terminating the instance cannot be undone.
            </div>
          </SpaceBetween>
        </Form>
      </form>
      </SpaceBetween>
    </Modal>
  );
};

export default TerminateInstanceModal;

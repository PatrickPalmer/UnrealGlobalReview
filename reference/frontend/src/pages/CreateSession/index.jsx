// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React, { useState, useCallback, useRef } from 'react';
import { HelpPanel, Wizard } from '@cloudscape-design/components';
import { Breadcrumbs, Navigation } from './wizard-components.jsx';
import Step1 from './stepComponents/step1.jsx';
import Step2 from './stepComponents/step2.jsx';
import Review from './stepComponents/step3.jsx';
import { DEFAULT_STEP_INFO, TOOLS_CONTENT } from './steps-config';
import ExternalLinkGroup from '../common/ExternalLinkGroup';
import InfoLink from '../common/InfoLink';
import Notifications from '../../components/Notifications';
import { CustomAppLayout } from '../common/common-components';
import SideNavigation from '@cloudscape-design/components/side-navigation';
import '../../styles/wizard.scss';
import { useNavigate } from 'react-router-dom';
import axiosInstance from '../../common/AxiosComm';
import { v4 as uuid4 } from 'uuid';

const steps = [
  {
    title: 'Specify Session Details',
    stateKey: 'details',
    StepContent: Step1,
  },
  {
    title: 'Select Unreal Engine level',
    stateKey: 'engine',
    StepContent: Step2,
  },
  {
    title: 'Review and Create',
    stateKey: 'review',
    StepContent: Review,
  },
];

export const checkSessionDetails = (session) => {
  if (!session['details']['ami']) {
    console.log("Missing AMI.");
    return false;
  } 
  else if (!session['details']['sessionName']) {
    console.log("Missing session name.");
    return false;
  }
  else if (!session['details']['region']) {
    console.log("Missing region.");
    return false;
  }
  else if (!session['details']['instanceClass']) {
    console.log("Missing instance class.");
    return false;
  }
  else if (!session['details']['duration']) {
    console.log("Missing duration.");
    return false;
  }
  else if (!session['engine']['stream']) {
    console.log("Missing stream.");
    return false;
  }
  else if (!session['engine']['uproject']) {
    console.log("Missing uproject.");
    return false;
  }
  else if (!session['engine']['umap']) {
    console.log("Missing umap.");
    return false;
  }
  else if (session['engine']['port'] == '') {
    console.log("Missing port.");
    return false;
  }
  else if (session['engine']['username'] == '') {
    console.log("Missing username.");
    return false;
  }
  else if (session['engine']['password'] == '') {
    console.log("Missing password.");
    return false;
  }
  else {
    console.log("All session info complete.")
    return true;
  }
};

const navItems = [
  { type: 'link', text: 'Sessions', href: '/sessions' },
  { type: 'link', text: 'Images', href: '/images' },
  { type: 'link', text: 'Stages', href: '/stages' },
  { type: 'link', text: 'Instances', href: '/instances' }
];


const i18nStrings = {
  submitButton: 'Create Session',
  nextButton: 'Next',
  previousButton: 'Previous',
  cancelButton: 'Cancel',
  stepNumberLabel: stepNumber => `Step ${stepNumber}`,
  collapsedStepsLabel: (stepNumber, stepsCount) => `Step ${stepNumber} of ${stepsCount}`,
  stepCounterText: (stepIndex, totalStepCount) => `Step ${stepIndex + 1}/${totalStepCount}`,
  taskTitle: (taskIndex, taskTitle) => `Task ${taskIndex + 1}: ${taskTitle}`,
  labelHotspot: (openState, stepIndex, totalStepCount) =>
    openState
      ? `close annotation for step ${stepIndex + 1} of ${totalStepCount}`
      : `open annotation for step ${stepIndex + 1} of ${totalStepCount}`,
  labelDismissAnnotation: 'hide annotation',
};

const getDefaultToolsContent = activeIndex => TOOLS_CONTENT[steps[activeIndex].stateKey].default;

const getFormattedToolsContent = tools => (
  <HelpPanel header={<h2>{tools.title}</h2>} footer={<ExternalLinkGroup items={tools.links} />}>
    {tools.content}
  </HelpPanel>
);

const useTools = () => {
  const [toolsContent, setToolsContent] = useState(getFormattedToolsContent(getDefaultToolsContent(0)));
  const [isToolsOpen, setIsToolsOpen] = useState(false);
  const appLayout = useRef();

  const setFormattedToolsContent = tools => {
    setToolsContent(getFormattedToolsContent(tools));
  };

  const setHelpPanelContent = tools => {
    if (tools) {
      setFormattedToolsContent(tools);
    }
    setIsToolsOpen(true);
    appLayout.current?.focusToolsClose();
  };
  const closeTools = () => setIsToolsOpen(false);

  const onToolsChange = evt => setIsToolsOpen(evt.detail.open);

  return {
    toolsContent,
    isToolsOpen,
    setHelpPanelContent,
    closeTools,
    setFormattedToolsContent,
    onToolsChange,
    appLayout,
  };
};

const useWizard = (closeTools, setFormattedToolsContent, notify) => {
  const [activeStepIndex, setActiveStepIndex] = useState(0);
  const [stepsInfo, setStepsInfo] = useState(DEFAULT_STEP_INFO);
  const navigate = useNavigate();

  const onStepInfoChange = useCallback(
    (stateKey, newStepState) => {
      setStepsInfo({
        ...stepsInfo,
        [stateKey]: {
          ...stepsInfo[stateKey],
          ...newStepState,
        },
      });
    },
    [stepsInfo]
  );

  const setActiveStepIndexAndCloseTools = index => {
    setActiveStepIndex(index);
    setFormattedToolsContent(getDefaultToolsContent(index));
    closeTools();
  };

  const onNavigate = evt => {
    setActiveStepIndexAndCloseTools(evt.detail.requestedStepIndex);
  };

  const onCancel = () => {
    console.log('Cancel');
    navigate("/sessions");
  };

  const onSubmit = () => {
    console.log("Creating Session.");
    console.log(stepsInfo);
    if (!checkSessionDetails(stepsInfo)) {
      notify("warn", "Please fill in all required session details.");
    } else {
      axiosInstance.post('/sessions', {
        Ami: stepsInfo['details']['ami'].value,  
        Region: stepsInfo['details']['region'].value,
        InstanceType: stepsInfo['details']['instanceClass'].value,
        Duration: stepsInfo['details']['duration'].value,
        Description: stepsInfo['details']['description'],
        UnrealProject: stepsInfo['engine']['uproject'].value,
        UnrealLevelName: stepsInfo['engine']['umap'].value,
        PerforceStream: stepsInfo['engine']['stream'].value,
        PerforcePort: stepsInfo['engine']['port'],
        PerforceUser: stepsInfo['engine']['username'],
        PerforcePassword: stepsInfo['engine']['password'],
        KeyName: stepsInfo['details']['keypair'].value,
        Name: stepsInfo['details']['sessionName']
      })
      .then(function (response) {
        console.log(response);
        if (response && response.data && response.data.session) {
          navigate('/sessions/' + response.data.session.Id);
        } else {
          navigate('/sessions');
        }
      })
      .catch(error => {
        console.log("ERROR");
        console.log(error);
        let why = undefined;
        try {
            why = error.response.data.detail;
        } catch(err) {}
        if (!why) {
            why = "Please fill in all required session details";
        }
        notify('error', `Error creating session: ${why}.`);
      });
    }
  };

  return {
    activeStepIndex,
    stepsInfo,
    setActiveStepIndexAndCloseTools,
    onStepInfoChange,
    onNavigate,
    onCancel,
    onSubmit,
  };
};

const CreateSession = () => {
  const [streams, setStreams] = useState({ streams: [], projects: [], levels: [], streams_state: "pending", projects_state: "pending"});

  // notifications
  const [notices, setNotices] = useState([]);
  const notify = (level, msg) => {
    setNotices([...notices, {id: uuid4(), level:level, msg:msg}]);
  };
  const notified = (id) => {
    setNotices(notices.filter(item => item.id !== id))
  };

  const {
    toolsContent,
    isToolsOpen,
    setHelpPanelContent,
    closeTools,
    setFormattedToolsContent,
    onToolsChange,
    appLayout,
  } = useTools();

  const {
    activeStepIndex,
    stepsInfo,
    setActiveStepIndexAndCloseTools,
    onStepInfoChange,
    onNavigate,
    onCancel,
    onSubmit,
  } = useWizard(closeTools, setFormattedToolsContent, notify);

  const wizardSteps = steps.map(({ title, stateKey, StepContent }) => ({
    title,
    info: <InfoLink onFollow={() => setHelpPanelContent(TOOLS_CONTENT[stateKey].default)} />,
    content: (
      <StepContent
        info={stepsInfo}
        onChange={newStepState => onStepInfoChange(stateKey, newStepState)}
        setHelpPanelContent={setHelpPanelContent}
        setActiveStepIndex={setActiveStepIndexAndCloseTools}
        notifyFn={notify}
        streams={streams}
        setStreams={setStreams}
      />
    ),
  }));

  const onSideFollow = e => {
    e.preventDefault();
    navigate(e.detail.href);
  };
  
  return (
    <CustomAppLayout
      ref={appLayout}
      navigation={
        <SideNavigation 
          header={{ href: '/sessions', text: 'Global Review' }} 
          onFollow={onSideFollow}  
          items={navItems} />}
      tools={toolsContent}
      toolsOpen={isToolsOpen}
      onToolsChange={onToolsChange}
      breadcrumbs={<Breadcrumbs/>}
      contentType="wizard"
      content={
        <Wizard
          steps={wizardSteps}
          activeStepIndex={activeStepIndex}
          i18nStrings={i18nStrings}
          onNavigate={onNavigate}
          onCancel={onCancel}
          onSubmit={onSubmit}
        />
      }
      notifications={<Notifications notices={notices} notifiedFn={notified}/>}
      stickyNotifications
    />
  );
};

export default CreateSession;
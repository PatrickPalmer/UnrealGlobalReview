// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React from 'react';

export const CLASS_OPTIONS = [
  {
    label: "G6",
    options: [
      {  
        label: "g6e.xlarge", 
        value: "g6e.xlarge",
        tags: ["4 vCPUs", "Memory: 32 GiB", "Storage: 1x250 GB"],
      },
      { 
        label: "g6e.2xlarge", 
        value: "g6e.2xlarge",
        tags: ["8 vCPUs", "Memory: 64 GiB", "Storage: 1x450 GB"] 
      },
      { 
        label: "g6e.4xlarge", 
        value: "g6e.4xlarge",
        tags: ["16 vCPUs", "Memory: 128 GiB", "Storage: 1x600 GB"] 
      },
      { 
        label: "g6e.8xlarge", 
        value: "g6e.8xlarge",
        tags: ["32 vCPUs", "Memory: 256 GiB", "Storage: 2x450 GB"] 
      }
    ]
  },
  {
    label: "G5",
    options: [
      {  
        label: "g5.xlarge", 
        value: "g5.xlarge",
        tags: ["4 vCPUs", "Memory: 16 GiB", "Storage: 1x250 GB"],
      },
      { 
        label: "g5.2xlarge", 
        value: "g5.2xlarge",
        tags: ["8 vCPUs", "Memory: 32 GiB", "Storage: 1x450 GB"] 
      },
      { 
        label: "g5.4xlarge", 
        value: "g5.4xlarge",
        tags: ["16 vCPUs", "Memory: 64 GiB", "Storage: 1x600 GB"] 
      },
      { 
        label: "g5.8xlarge", 
        value: "g5.8xlarge",
        tags: ["32 vCPUs", "Memory: 128 GiB", "Storage: 1x900 GB"] 
      }
    ]
  },
  {
    label: "G4dn",
    options: [
      { 
        label: "g4dn.2xlarge", 
        value: "g4dn.2xlarge",
        tags: ["8 vCPUs", "Memory: 32 GiB", "Storage: 1x225 GB"] 
      },
      { 
        label: "g4dn.4xlarge", 
        value: "g4dn.4xlarge",
        tags: ["16 vCPUs", "Memory: 64 GiB", "Storage: 1x225 GB"] 
      },
      { 
        label: "g4dn.8xlarge", 
        value: "g4dn.8xlarge",
        tags: ["32 vCPUs", "Memory: 128 GiB", "Storage: 1x900 GB"] 
      }
    ]
  },
];

export const DURATION_OPTIONS = [
  { label: "2 hours", value: "PT2H" },
  { label: "4 hours", value: "PT4H" },
  { label: "8 hours", value: "PT8H" },
  { label: "12 hours", value: "PT12H" },
  { label: "16 hours", value: "PT16H" },
  { label: "24 hours", value: "PT24H" },
];

export const DEFAULT_STEP_INFO = {
  engine: {
    username: '',
    port: '',
    // stream: {label: null, value: ''},
    // uproject: {label: '...', value: ''},
    // umap: {label: '...', value: ''},
  },
  details: {
    // instanceClass: {label: '...', value: ''},
    // region: {label: '...', value: ''},
    keypair: {label: 'None', value: ''},
    // ami: {label: '...', value: ''},
    // duration: {label: '...', value: ''},
    description: '',
  }
};

export const TOOLS_CONTENT = {
  engine: {
    default: {
      title: 'Unreal Engine Level',
      content: (
        <div>
          <p>
            Connect to the Perforce server using your p4 login credentials. <br></br><br></br>
            Then, choose the stream that contains your Unreal Engine project files. <br></br><br></br>
            After the stream is chosen, select the Unreal Engine project & level.
          </p>
        </div>
      ),
      links: [
        {
          href: 'https://www.unrealengine.com/en-US',
          text: 'Unreal Engine',
        },
        {
          href: 'https://www.perforce.com/products/helix-core',
          text: 'Perforce Helix Core',
        }
      ],
    },
  },
  details: {
    default: {
      title: 'Session Details',
      content: (
        <p>
          Specify the details for the review session. <br></br><br></br>
          You must first register an AMI on the <b>Images</b> page before making your AMI selection.
        </p>
      ),
      links: [
        {
          href: 'https://aws.amazon.com/ec2/instance-types/g5/',
          text: 'Amazon EC2 G5 Instances',
        },
        {
          href: 'https://aws.amazon.com/ec2/instance-types/g4/',
          text: 'Amazon EC2 G4 Instances',
        }
      ],
    },
  },
  review: {
    default: {
      title: 'Review and Create',
      content: (
        <div>
          <p>
            Verify your settings for your session, and edit the settings as needed. When you are satisfied with your
            settings, choose <b>Create Session</b>.
          </p>
          <p>
            After Global Review creates your session, the new session appears in the list of sessions.
            The session has a status of <b>In Progress</b> until the instance is ready to use. When the state changes
            to <b>Success</b>, you can connect to the instance.
          </p>
          <p>
            It can take up to 20 minutes before the new session is available.
          </p>
        </div>
      ),
      links: [
        {
          href: 'https://www.unrealengine.com/en-US',
          text: 'Unreal Engine',
        },
      ],
    },
  },
};

export const TIME_ZONES = [
  {
    label: 'No preference',
    value: '1',
  },
  {
    label: 'AUS Central Standard Time',
    value: '2',
  },
  {
    label: 'AUS Eastern Standard Time',
    value: '3',
  },
  {
    label: 'Afghanistan Standard Time',
    value: '4',
  },
  {
    label: 'Alaskan Standard Time',
    value: '5',
  },
  {
    label: 'Atlantic Standard Time',
    value: '6',
  },
  {
    label: 'Belarus Standard Time',
    value: '7',
  },
  {
    label: 'Cananda Central Standard Time',
    value: '8',
  },
  {
    label: 'Cananda Eastern Standard Time',
    value: '9',
  },
];
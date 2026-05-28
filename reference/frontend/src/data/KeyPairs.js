// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import axiosInstance from "../common/AxiosComm";
import { useQueryClient } from '@tanstack/react-query';


const KeyPairsCacheName = "keypairs";

const getKeyPairs = async () => { 
  const response = await axiosInstance.get('/keypairs');
  return response.data['keypair'];
}

const clearKeyPairsCache = () => {
  const queryClient = useQueryClient();
  queryClient.invalidateQueries({ queryKey: [ KeyPairsCacheName ]});
}

const processKeypairIntoUxOptions = (keypairs) => {
  let keypairList = [{label: 'None', value: ''}];
  if (keypairs) {
    for (let i = 0; i < keypairs.length; i++) {
      keypairList.push({
        label: keypairs[i].KeyName,
        value: keypairs[i].KeyName
      });
    }
  }
  return keypairList;
};

export { KeyPairsCacheName, 
         getKeyPairs,
         clearKeyPairsCache,
         processKeypairIntoUxOptions };


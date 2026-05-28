// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import axiosInstance from "../common/AxiosComm";
import { useQueryClient } from '@tanstack/react-query';


const AvailableRegionsCacheName = "availableRegions";

const getAvailableRegions = async () => { 
  const response = await axiosInstance.get('/config/regions/available');
  return response.data['region'];
}

const clearAvailableRegionsCache = () => {
  const queryClient = useQueryClient();
  queryClient.invalidateQueries({ queryKey: [ AvailableRegionsCacheName ]});
}

const processRegionsIntoUxOptions = (regions) => {
  if (!regions) {
    return [];
  }
  let processed = {};
  for (let i = 0; i < regions.length; i++) {
    let region_name = regions[i].RegionName.split(" (")[0];
    if (region_name.substring(0,3) === "US ") {
      region_name = "US";
    }
    if (!(region_name in processed)) {
      processed[region_name] = [];
    }
    processed[region_name].push({'label': regions[i].RegionName, value: regions[i].RegionId})
  }
  return Object.keys(processed).map(x => {
    return {
      'label': x,
      'options': processed[x]
    }
  });
};

export { AvailableRegionsCacheName, 
         getAvailableRegions,
         clearAvailableRegionsCache,
         processRegionsIntoUxOptions };


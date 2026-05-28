// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import axiosInstance from "../common/AxiosComm";
import { useQueryClient, useMutation } from '@tanstack/react-query';


const ImagesCacheName = "amiImages";

const getImages = async () => { 
  const response = await axiosInstance.get('/images');
  return response.data['image'];
}

const addImage = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (newImage) => {
      return axiosInstance.post('/images', newImage);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [ ImagesCacheName ]});
    },
  });
};
  
const clearImagesCache = () => {
  const queryClient = useQueryClient();
  queryClient.invalidateQueries({ queryKey: [ ImagesCacheName ]});
}

const processImagesIntoUxOptions = (images) => {
  if (!images) {
    return [];
  }
  let amiList = [];
  for (let i = 0; i < images.length; i++) {
    amiList.push({
      label: images[i].Name + " (" + images[i].Ami + ")",
      value: images[i].Ami
    });
  }
  return amiList;
};

export { ImagesCacheName, 
         addImage,
         getImages,
         clearImagesCache,
         processImagesIntoUxOptions };


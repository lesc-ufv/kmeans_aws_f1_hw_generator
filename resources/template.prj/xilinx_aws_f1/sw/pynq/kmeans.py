import pynq
import sys
import numpy as np
import random
import time
from datetime import timedelta
from math import ceil

class KmeansHLS(pynq.DefaultIP):
    """
        Driver for kmeans HLS kernel.
    """
    
    bindto  = ["xilinx.com:hls:workload_1:1.0"]
    
    def __init__(self,description):
        super().__init__(description=description)
        self._fullpath = description['fullpath']
        self.cluster_buffer = []
        self.input_buffer = []
        self.output_buffer = []
    
    def allocate(self, k, n, num_points):       
        self.cluster_buffer = pynq.allocate((k*n,),dtype=np.ushort)    
        self.input_buffer = pynq.allocate((num_points*n,),dtype=np.ushort)
        self.output_buffer = pynq.allocate((num_points,),dtype=np.int)
        
    def classify(self, k, n, clusters, data):        
        flat_clusters =  np.array(clusters,dtype=np.ushort).flatten()
        if len(data) > 0:
            self.allocate(k, n, len(data)) 
            self.input_buffer[:] = np.array(data,dtype=np.ushort).flatten()
            self.input_buffer.sync_to_device() 
            
        self.cluster_buffer[:] = flat_clusters
        self.cluster_buffer.sync_to_device()        
        self.call(self.cluster_buffer,self.input_buffer, self.output_buffer)
        self.output_buffer.sync_from_device()
               
        return self.output_buffer
    
    
class KmeansHw(pynq.DefaultIP):
    """
        Driver for kmeans RTL kernel.
    """
    
    bindto  = ["xilinx.com:RTLKernel:kernel_top:1.0"]
    
    def __init__(self,description):
        super().__init__(description=description)
        self._fullpath = description['fullpath']
        self.input_buffer = []
        self.output_buffer = []
    
    def allocate(self, k, n, num_points):
        num_config_bytes = 64
        num_cluster_bytes = int(ceil((k*n*8.0)/64.0)*64.0)
        num_points_bytes = int(ceil((num_points * n * 2.0)/64.0)*64.0)
        total_in_bytes = num_config_bytes+num_cluster_bytes+num_points_bytes
        total_out_bytes = int(ceil(num_points_bytes/(2 * n)/64.0)*64.0)
        self.input_buffer = pynq.allocate((total_in_bytes,),dtype=np.byte)
        self.output_buffer = pynq.allocate((total_out_bytes,),dtype=np.byte)
        
    def flat_clusters(self,c):
        flat_c = np.array(c,dtype='u4').flatten()
        flat_idx = np.array([i for i in range(1,len(flat_c)+1)],dtype='u4')
        flat_with_idx_clusters = np.array(list(zip(flat_idx,flat_c)),dtype='u4').flatten().tobytes()
        return list(flat_with_idx_clusters)
    
    def flat_data(self, d):
        return list(np.array(d,dtype='u2').flatten().tobytes())
    
    def classify(self, k, n, clusters, data):        
        flat_with_idx_clusters = self.flat_clusters(clusters)  
        if len(data) > 0:
            self.allocate(k, n, len(data)) 
            flat_data = self.flat_data(data)
            self.input_buffer[64+len(flat_with_idx_clusters):64+len(flat_with_idx_clusters)+len(flat_data)] = flat_data
            self.input_buffer[64+len(flat_with_idx_clusters):64+len(flat_with_idx_clusters)+len(flat_data)].sync_to_device() 
            
        self.input_buffer[0:64] = list(int(k * n).to_bytes(64,sys.byteorder))
        self.input_buffer[64:64+len(flat_with_idx_clusters)] = flat_with_idx_clusters
        self.input_buffer[0:64+len(flat_with_idx_clusters)].sync_to_device()        
        self.call(len(self.input_buffer), len(self.output_buffer),self.input_buffer, self.output_buffer)
        self.output_buffer.sync_from_device()
               
        return self.output_buffer
       
    
class KMeansFPGA():
    def __init__(self, n_clusters, n_dims, max_iter = 10, xclbin=''):
        self._xclbin = xclbin
        self._n_clusters = n_clusters
        self._n_dims = n_dims
        self._max_iter = max_iter
        self.ol = pynq.Overlay(xclbin)
        self.kmeans_hw = self.ol.kernel_top_1
        
    def fit(self, X):
        self.clusters = [ [j if i == 0 else 0 for i in range(self._n_dims)] for j in range(self._n_clusters) ]     
        clusters_old = self.clusters
        
        pred = self.kmeans_hw.classify(self._n_clusters,self._n_dims,self.clusters,X)
        
        flat_data = np.array(X).flatten()
        num_point = len(X)
        
        k_sum = np.ndarray((self._n_clusters*self._n_dims,), dtype=int)
        k_avg = np.ndarray((self._n_clusters,), dtype=int)
              
        for it in range(self._max_iter):
            k_sum.fill(0)
            k_avg.fill(0)
            for i in range(num_point):
                for j in range(self._n_dims):
                     k_sum[pred[i] * self._n_dims + j] += flat_data[i * self._n_dims + j]
                k_avg[pred[i]] += 1
            
            different = 0
            for j in range(self._n_clusters):
                for d in range(self._n_dims):
                    idx = j * self._n_dims + d
                    if k_avg[idx // self._n_dims] > 0:
                        self.clusters[j][d] = int(k_sum[idx] // k_avg[idx // self._n_dims])
      
                    if self.clusters[j][d] != clusters_old[j][d]:
                        different = 1;

                    clusters_old[j][d] = self.clusters[j][d];
            
            if different == 0:
                pred = self.kmeans_hw.classify(self._n_clusters,self._n_dims,self.clusters,[])
            else:
                break
                
        return self
    
     
    def predict(self, X):
        pred = self.kmeans_hw.classify(self._n_clusters,self._n_dims,self.clusters,X)
        return np.array(pred[:len(X)],dtype=int)
        
    def free(self):
        self.ol.free()
        
        
    
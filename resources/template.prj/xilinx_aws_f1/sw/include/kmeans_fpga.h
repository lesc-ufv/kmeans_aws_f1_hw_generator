#include <cstring>
#include <iostream>
#include <fstream>
#include <sstream>
#include <chrono>
#include <vector>
#include <string>
#include <cmath>

#include "timer.h"
#include "xcl2.hpp"

#define NUM_CHANNELS 1
#define NUM_HW_INPUT 32
#define DATA_INPUT_HW_BITS 16
#define DATA_OUTPUT_HW_BITS 8
#define CLUSTER_HW_BITS 64
#define CL1 512
#define CL4 2048
#define INITIAL_CONF_ID 0
#define INITIAL_CLUSTER_ID 64

//Timers

#define INIT_TIMER_ID 0
#define ALLOCATE_TIMER_ID 1
#define RD_FILE_TIMER_ID 2
#define CLUSTERING_TIMER_ID 3
#define PROCESS_TIMER_ID 4

using namespace std;
using namespace std::chrono;

typedef unsigned char byte;
typedef unsigned short uint16;

class KmeansFpga{
    
private:
  cl::Context m_context;
  cl::CommandQueue m_q;
  cl::Program m_prog;
  cl::Kernel m_kernel;
  size_t m_input_size_bytes;
  size_t m_output_size_bytes;
  cl::Buffer m_input_buffer;
  cl::Buffer m_output_buffer;
  cl_int err;
     
  int m_num_points;
  int m_num_clusters;
  int m_num_dims;
  
  int m_config_bytes;
  double m_cluster_bytes;
  double m_points_bytes;
  
  byte *m_main_data;
  int *m_num_conf;
  int *m_clusters;
  int *m_clusters_old;
  
  uint16 *m_input_data;
  byte *m_output_data;
  
  void kmeans_process();
  
  void kmeans_set_args();

public:
        
      int kmeans_fpga_init(std::string &binary_file);
    
      int read_file(std::string &data_file);
      
      void kmeans_clustering(int max_iterations, std::string &output_file);
      
      int kmeans_allocate(int num_points, int num_cluster, int num_dim);
      
      int kmeans_deallocate();
      
      int kmeans_print_report();
    
};

#include "kmeans_fpga.h"

TIMER_INIT(7);

int KmeansFpga::kmeans_fpga_init(std::string &binary_file){

  TIMER_START(INIT_TIMER_ID);
  cl_int err;
  // get_xil_devices() is a utility API which will find the xilinx
  // platforms and will return list of devices connected to Xilinx platform
  auto devices = xcl::get_xil_devices();
  // read_binary_file() is a utility API which will load the binary_file
  // and will return the pointer to file buffer.
  auto fileBuf = xcl::read_binary_file(binary_file);
  cl::Program::Binaries bins{{fileBuf.data(), fileBuf.size()}};
  bool valid_device = false;
  for (unsigned int i = 0; i < devices.size(); i++) {
    auto device = devices[i];
    // Creating Context and Command Queue for selected Device
    OCL_CHECK(err, m_context = cl::Context(device, NULL, NULL, NULL, &err));
    OCL_CHECK(err, m_q = cl::CommandQueue(m_context, device, CL_QUEUE_PROFILING_ENABLE | CL_QUEUE_OUT_OF_ORDER_EXEC_MODE_ENABLE, &err));

    std::cout << "Trying to program device[" << i
              << "]: " << device.getInfo<CL_DEVICE_NAME>() << std::endl;
    m_prog = cl::Program(m_context, {device}, bins, NULL, &err);
    if (err != CL_SUCCESS) {
      std::cout << "Failed to program device[" << i << "] with xclbin file!\n";
    } else {
      std::cout << "Device[" << i << "]: program successful!\n";
      valid_device = true;
      break; // we break because we found a valid device
    }
  }
  
  if (!valid_device) {
    std::cout << "Failed to program any device found, exit!\n";
    exit(EXIT_FAILURE);
  }

  OCL_CHECK(err, m_kernel = cl::Kernel(m_prog,"kernel_top", &err));

  TIMER_STOP_ID(INIT_TIMER_ID);

  return 0;    
    
}

int KmeansFpga::kmeans_allocate(int num_points, int num_clusters, int num_dims){
    
    TIMER_START(ALLOCATE_TIMER_ID);
    
    m_iteration_count = 0;
    m_num_points = num_points;
    m_num_dims = num_dims;
    m_num_clusters = num_clusters;
      
    m_config_bytes = 64; //aligned in 64 bytes
    m_cluster_bytes = std::ceil((num_clusters * num_dims * 8.0)/64.0)*64.0; //aligned in 64 bytes
    m_points_bytes = std::ceil((num_points * num_dims * 2.0)/64.0)*64.0;   //aligned in 64 bytes
    m_input_size_bytes = (size_t)(m_config_bytes + m_cluster_bytes + m_points_bytes);//aligned in 64 bytes
    
    
    //(((m_points_bytes/64)/(512/((512/16/num_dims)*8))) * 64);
    //               |                  |                   |____ acelerator input size in bytes
    //               |                  |________________________ acerarator output size per input
    //               |___________________________________________ number of inputs to acelerator
        
    m_output_size_bytes = (size_t)(std::ceil(m_points_bytes/(2 * m_num_dims)/64.0)*64.0);//simplification of the formula above and aligned to 64 bytes
    
    posix_memalign((void**)&m_main_data,4096,m_input_size_bytes); //m_main_data = (byte *) malloc(m_input_size_bytes);
    posix_memalign((void**)&m_clusters_old,4096,sizeof(int) * num_clusters * num_dims);//m_clusters_old = (int *) malloc(sizeof(int) * num_clusters * num_dims);
    posix_memalign((void**)&m_output_data,4096,m_output_size_bytes);//m_output_data = (byte *) malloc(m_output_size_bytes);
    
    m_num_conf = (int *) &m_main_data[INITIAL_CONF_ID];
    m_clusters = (int *) &m_main_data[INITIAL_CLUSTER_ID];
    m_num_conf[0] = (num_clusters * num_dims);

    int idx = m_config_bytes+m_cluster_bytes;
    m_input_data = (uint16 *) &m_main_data[idx];
    
   OCL_CHECK(err, m_input_buffer = cl::Buffer(m_context, CL_MEM_ALLOC_HOST_PTR | CL_MEM_READ_ONLY, m_input_size_bytes, NULL, &err));
   OCL_CHECK(err, m_output_buffer = cl::Buffer(m_context, CL_MEM_ALLOC_HOST_PTR | CL_MEM_WRITE_ONLY, m_output_size_bytes, NULL, &err));
   
   TIMER_STOP_ID(ALLOCATE_TIMER_ID);
      
   return 0;
}

int KmeansFpga::kmeans_deallocate(){
    free(m_main_data);
    free(m_clusters_old);
    free(m_output_data);
    return 0;
}

int KmeansFpga::read_file(std::string &data_file){
    TIMER_START(RD_FILE_TIMER_ID);
    //reading input data
    std::string line;
    std::ifstream data_in(data_file);
    int data_idx = 0;
    int counter_points = 0;
    while (std::getline(data_in, line)) {
        //uncoment if data is separated by ','
        for (int i = 0, n = line.length(); i < n; i++) {
            if (line[i] == ',') {
                line[i] = ' ';
            }
        }
        std::istringstream iss(line);
        int a;
        //exception - the first data is not desirable
        //please comment next line if it is desireble
        iss >> a;
        for (int j = 0; (iss >> a); j++) {
            m_input_data[data_idx] = (short) a;
            data_idx++;
            if (j + 1 == m_num_dims) {
                break;
            }
        }
        counter_points++;
        if (counter_points >= m_num_points) {
            break;
        }
    }
    data_in.close();
    TIMER_STOP_ID(RD_FILE_TIMER_ID);
    return 0;
}

void KmeansFpga::kmeans_clustering(int max_iterations, std::string &output_file){
      
  TIMER_START(CLUSTERING_TIMER_ID);
  
  kmeans_set_args();
  
  TIMER_START(FIRST_CPY_TIMER_ID);
     // Write features to the device
  OCL_CHECK(err, err = m_q.enqueueWriteBuffer(m_input_buffer, CL_TRUE, 0,
                                              m_input_size_bytes,
                                              m_main_data, NULL, NULL));

  OCL_CHECK(err, err = m_q.enqueueMigrateMemObjects({m_input_buffer}, 0, NULL, NULL));
  
  m_q.finish();
  
  TIMER_STOP_ID(FIRST_CPY_TIMER_ID);
  
  int c_hw_idx = 1;
  // adding the initial clusters
  for (int i = 0; i < m_num_clusters; i++) {
      for (int j = 0; j < m_num_dims; j++) {
          int value;
          if (j == 0) {
              value = i;
          } else {
              value = 0;
          }
          int c_idx = (i * 2 * m_num_dims) + (j * 2);
          m_clusters[c_idx + 0] = c_hw_idx;
          m_clusters[c_idx + 1] = value;
          m_clusters_old[(i * m_num_dims) + j] = value;
          c_hw_idx++;
      }
  }
  //start kmeans
  int it;
  int k_sum[m_num_clusters * m_num_dims];
  int k_avg[m_num_clusters];
  
  for (it = 0; it < max_iterations; it++) {
      memset(k_sum, 0, sizeof(int) * (m_num_clusters * m_num_dims));
      memset(k_avg, 0, sizeof(int) * m_num_clusters);
      
      //call hw kmeans process
      kmeans_process();
      
      //clusters update
      TIMER_START(UPDATE_CLUSTER_TIMER_ID);
      for (int i = 0; i < m_num_points; i++) {
          for (int j = 0; j < m_num_dims; j++) {
              k_sum[m_output_data[i] * m_num_dims + j] += m_input_data[i * m_num_dims + j];
          }
          k_avg[m_output_data[i]]++;
      }
         
      int different = 0;
      for (int j = 0, n=m_num_clusters * m_num_dims; j < n; j++) {
          if (k_avg[j / m_num_dims] > 0) {
              m_clusters[j * 2 + 1] = k_sum[j] / k_avg[j / m_num_dims];
          }
          if (m_clusters[j * 2 + 1] != m_clusters_old[j]) {
              different = 1;
          }
          m_clusters_old[j] = m_clusters[j * 2 + 1];
      }
      TIMER_STOP_ID(UPDATE_CLUSTER_TIMER_ID);
      
      if (different == 0) {
          break;
      }
  }
  TIMER_STOP_ID(CLUSTERING_TIMER_ID);
  
  
  std::string output_text = "Break in iteration " + std::to_string(it + 1) + "\n";
  for (int j = 0; j < m_num_clusters * m_num_dims; j++) {
      if (j % m_num_dims == 0) {
          output_text += "\nCluster values: ";
      }
      output_text += std::to_string(m_clusters[j * 2 + 1]) + " ";
  }
  std::ofstream data_out;
  data_out.open(output_file);
  data_out << output_text + "\n";
  data_out.close();

}

void KmeansFpga::kmeans_set_args(){
    
    OCL_CHECK(err, err = m_kernel.setArg(0, sizeof(cl_int),(void *)& m_input_size_bytes));
    OCL_CHECK(err, err = m_kernel.setArg(1, sizeof(cl_int),(void *)& m_output_size_bytes));
    OCL_CHECK(err, err = m_kernel.setArg(2, m_input_buffer));
    OCL_CHECK(err, err = m_kernel.setArg(3, m_output_buffer)); 
        
}

void KmeansFpga::kmeans_process(){
 
    
    TIMER_START(PROCESS_TIMER_ID);
    
    OCL_CHECK(err, err = m_q.enqueueWriteBuffer(m_input_buffer, CL_TRUE, 0,
                                                m_config_bytes + m_cluster_bytes, //No need to send the points again, just the clusters
                                                m_main_data, NULL, NULL));
    
    OCL_CHECK(err, err = m_q.enqueueTask(m_kernel, NULL, NULL));
    
    m_q.finish();

    // Schedule the reading of new memberships values back to the host
    OCL_CHECK(err, err = m_q.enqueueReadBuffer(m_output_buffer, CL_TRUE, 0,
                                               m_output_size_bytes,
                                               m_output_data, NULL, NULL));
    TIMER_STOP_ID(PROCESS_TIMER_ID);
    
    if(m_iteration_count == 0)
        m_first_it = TIMER_REPORT_MS(PROCESS_TIMER_ID);
    
    m_iteration_count++;
}

int KmeansFpga::kmeans_print_report() {

    printf("------------------------------------------------------\n");
    printf("  Performance Summary                                 \n");
    printf("------------------------------------------------------\n");
    printf("  Read input file            : %12.4f ms\n", TIMER_REPORT_MS(RD_FILE_TIMER_ID));
    printf("  Device Initialization      : %12.4f ms\n", TIMER_REPORT_MS(INIT_TIMER_ID));
    printf("  Buffer Allocation          : %12.4f ms\n", TIMER_REPORT_MS(ALLOCATE_TIMER_ID));
    printf("  Iteration:                 : %12.4f ms\n", TIMER_REPORT_MS(PROCESS_TIMER_ID));
    printf("  Iteration count            : %16d     \n", m_iteration_count);
    printf("  Update clusters            : %12.4f ms\n", TIMER_REPORT_MS(UPDATE_CLUSTER_TIMER_ID));
    printf("  Clusterization             : %12.4f ms\n", TIMER_REPORT_MS(CLUSTERING_TIMER_ID));
    printf("------------------------------------------------------\n");
    
    std::ofstream csv;
    csv.open("out.csv",std::ofstream::out | std::ofstream::app);
    csv << m_first_it << "," << TIMER_REPORT_MS(FIRST_CPY_TIMER_ID) << "," << TIMER_REPORT_MS(PROCESS_TIMER_ID) << "," <<  TIMER_REPORT_MS(UPDATE_CLUSTER_TIMER_ID) << "," << TIMER_REPORT_MS(CLUSTERING_TIMER_ID) << "," << m_iteration_count << "," <<  m_num_clusters << "," <<  m_num_dims << std::endl;
    csv.close();

  return 0;
}

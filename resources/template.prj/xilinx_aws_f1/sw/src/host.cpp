#include "host.h"

int main(int argc, char **argv) {

    int num_points = 10;
    int max_iterations = 10;
    int num_clusters = 2;
    int num_dim = 2;
    std::string data_in_file_path, output_file, output_text;
    std::string line;
    std::string binaryFile;
    
    if (argc > 6) {
        binaryFile = argv[1];
        num_points = atoi(argv[2]);
        num_clusters = atoi(argv[3]);
        max_iterations = atoi(argv[4]);
        num_dim = atoi(argv[5]);
        data_in_file_path = argv[6];
        output_file = "./kmeans_" + std::to_string(num_points) + "_" + std::to_string(num_clusters) +
                      "_" + std::to_string(num_dim) + "_out_fpga" + ".txt";
    } else {
        std::cout << "invalid args!!!\n";
        std::cout << "usage: <xclbin> <num_points> <num_clusters>  <max_iterations> <num_dim> <data_file>\n";
        exit(255);
    }

    //starting
    printf("%s Starting...\n", argv[0]);


    //It provides that only quantities of multiple values of CL1 are accepted.
    int max_amount_input_data = ((int) ((num_points * num_dim * DATA_INPUT_HW_BITS) / CL1)) * CL1 / (num_dim * DATA_INPUT_HW_BITS);
    //The line that contains the number of clusters to be set
    int total_initial_config_lines = 1;

    //The number of HARP 512b lines necessary to send clusters data
    int total_config_clusters_lines =
            ((num_clusters * num_dim * CLUSTER_HW_BITS) + CL1 - 1) / CL1;//ceil to num configuration lines;

    int total_input_data = max_amount_input_data * num_dim;

    //The number of HARP 512b lines necessary to send data to be processed
    int total_input_data_lines = (total_input_data * DATA_INPUT_HW_BITS) / CL1;

    int initial_input_data_id = INITIAL_CLUSTER_ID + (total_config_clusters_lines * CL1 / 8);

    //The number of HARP 512b lines necessary to send everything to HARP
    int total_input_lines = total_initial_config_lines + total_config_clusters_lines + total_input_data_lines;

    int total_output_data = (NUM_HW_INPUT / num_dim) * total_input_data_lines;


    //Creating main vector
    int total_main_vector = (total_input_lines * CL1 / 8);
    size_t total_main_vector_bytes = (sizeof(char) * total_main_vector);
    char *main_vector = (char *) malloc(total_main_vector_bytes);
    memset(main_vector, 0, total_main_vector_bytes);
    
    //Creating pointers for input/output data and clusters configurations
    int *initial_conf = (int *) &main_vector[INITIAL_CONF_ID];
    int *clusters = (int *) &main_vector[INITIAL_CLUSTER_ID];
    int *clusters_old = (int *) malloc(sizeof(int) * num_clusters * num_dim);
    short *input_data = (short *) &main_vector[initial_input_data_id];
    char *output_data = (char *) malloc(sizeof(char) * total_output_data);

    initial_conf[0] = num_clusters * num_dim;

    //reading input data
    std::ifstream data_in(data_in_file_path);
    int data_idx = 0;
    int counter_points = 0;
    while (std::getline(data_in, line)) {

        //uncoment if data is separated by ','
        for (int i = 0; i < line.length(); i++) {
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
            input_data[data_idx] = (short) a;
            data_idx++;
            if (j + 1 == num_dim) {
                break;
            }
        }

        counter_points++;

        if (counter_points >= num_points) {
            break;
        }
    }
    data_in.close();

    double time_sum = 0;
    double num_sum = 0;

    output_text = "";
    for (int times = 0; times < 11; times++) {

        int c_hw_idx = 1;
        // adding the initial clusters
        for (int i = 0; i < num_clusters; i++) {
            for (int j = 0; j < num_dim; j++) {
                int value;
                if (j == 0) {
                    value = i;
                } else {
                    value = 0;
                }
                int c_idx = (i * 2 * num_dim) + (j * 2);
                clusters[c_idx + 0] = c_hw_idx;
                clusters[c_idx + 1] = value;
                clusters_old[(i * num_dim) + j] = value;
                c_hw_idx++;
            }
        }

        if (times == 10) {
            output_text +=
                    "\n" + kmeans_process(binaryFile,true, main_vector, total_main_vector, output_data, total_output_data) +
                    "\n\n";
            continue;
        }

        //start timer
        high_resolution_clock::time_point s;
        duration<double> diff{};
        s = high_resolution_clock::now();

        //start kmeans
        int it;
        int k_sum[num_clusters * num_dim];
        int k_avg[num_clusters];

        for (it = 0; it < max_iterations; it++) {
            //memset(output_data, (char) -1, sizeof(char) * total_output_data);
            memset(k_sum, 0, sizeof(int) * (num_clusters * num_dim));
            memset(k_avg, 0, sizeof(int) * num_clusters);

            //chamar kmeans process
            kmeans_process(binaryFile,false, main_vector, total_main_vector, output_data, total_output_data);

            //clusters update
            for (int i = 0; i < total_output_data; i++) {
                for (int j = 0; j < num_dim; j++) {
                    k_sum[output_data[i] * num_dim + j] += input_data[i * num_dim + j];
                }
                k_avg[output_data[i]]++;
            }
            int different = 0;
            for (int j = 0; j < num_clusters * num_dim; j++) {
                if (k_avg[j / num_dim] > 0) {
                    clusters[j * 2 + 1] = k_sum[j] / k_avg[j / num_dim];
                }
                if (clusters[j * 2 + 1] != clusters_old[j]) {
                    different = 1;
                }
                clusters_old[j] = clusters[j * 2 + 1];
            }

            if (different == 0) {
                break;
            }
        }

        //stopping timer
        diff = high_resolution_clock::now() - s;
        double timeExec = diff.count();

        if (times == 0) {
            output_text = output_text + "Break in iteration " + std::to_string(it + 1) + "\n\n";
            for (int j = 0; j < num_clusters * num_dim; j++) {
                if (j % num_dim == 0) {
                    output_text += "\n\nCluster values: ";
                }
                output_text += std::to_string(clusters[j * 2 + 1]) + " ";
            }
            output_text += "\n\nTimes: ";
        }

        output_text += std::to_string(timeExec * 1000) + "ms ";
        if (times > 2) {
            time_sum += timeExec * 1000;
            num_sum++;
        }
    }

    output_text += "\n\nTime AVG (3º until 10º): " + std::to_string(time_sum / num_sum) + "ms ";

    std::ofstream data_out;
    data_out.open(output_file);

    data_out << output_text + "\n";

    // free host memory
    free(main_vector);
    free(clusters_old);
    free(output_data);

    //finishing
    printf("%s Finished...\n", argv[0]);

}

std::string kmeans_process(std::string binaryFile, bool debug, char *main_vector, int total_main_vector_bytes, char *output_data, int total_output_data){
    
    
    vector_u8 input;
    vector_u8 output;
    high_resolution_clock::time_point s;
    duration<double> diff{};
    double timeExec;
    std::string str_return = "";
    cl_int err;
	cl::CommandQueue q;
	cl::Context context;
	cl::Kernel kernel_top;
   
    for(int i=0;i < total_main_vector_bytes;i++)
        input.push_back(main_vector[i]);
    
    for(int i=0;i < total_output_data;i++)
        output.push_back(output_data[i]);
    
    
	// OPENCL HOST CODE AREA START
	// Create Program and Kernel
	
	auto devices = xcl::get_xil_devices();

	// read_binary_file() is a utility API which will load the binaryFile
	// and will return the pointer to file buffer.
	auto fileBuf = xcl::read_binary_file(binaryFile);
	cl::Program::Binaries bins { { fileBuf.data(), fileBuf.size() } };
	bool valid_device = false;
	for (unsigned int i = 0; i < devices.size(); i++) {
		auto device = devices[i];
		// Creating Context and Command Queue for selected Device
		OCL_CHECK(err, context = cl::Context(device, NULL, NULL, NULL, &err));
		OCL_CHECK(err,
				q = cl::CommandQueue(context, device, CL_QUEUE_PROFILING_ENABLE, &err));

		std::cout << "Trying to program device[" << i << "]: "
				<< device.getInfo<CL_DEVICE_NAME>() << std::endl;
		cl::Program program(context, { device }, bins, NULL, &err);
		if (err != CL_SUCCESS) {
			std::cout << "Failed to program device[" << i
					<< "] with xclbin file!\n";
		} else {
			std::cout << "Device[" << i << "]: program successful!\n";
			OCL_CHECK(err,
					kernel_top = cl::Kernel(program, "kernel_top",
							&err));
			valid_device = true;
			break; // we break because we found a valid device
		}
	}
	if (!valid_device) {
		std::cout << "Failed to program any device found, exit!\n";
		exit(EXIT_FAILURE);
	}

    std::vector<cl::Memory> buffer_r(NUM_CHANNELS);
    std::vector<cl::Memory> buffer_w(NUM_CHANNELS);

	// Allocate Buffer in Global Memory
	for (int i = 0; i < NUM_CHANNELS; ++i) {
        
        OCL_CHECK(err,buffer_r[i] = cl::Buffer(context, CL_MEM_USE_HOST_PTR | CL_MEM_READ_ONLY,
                                               total_main_vector_bytes, input.data(), &err));
        OCL_CHECK(err, buffer_w[i] = cl::Buffer(context, CL_MEM_USE_HOST_PTR | CL_MEM_WRITE_ONLY,
                                                total_output_data, output.data(), &err));
	}

    // 	Set the Kernel Arguments
	int arg_id = (NUM_CHANNELS * 2);
	for (int i = 0; i < NUM_CHANNELS; ++i) {
		OCL_CHECK(err, err = kernel_top.setArg(i, total_main_vector_bytes));
		OCL_CHECK(err, err = kernel_top.setArg(i+NUM_CHANNELS, total_output_data));
		OCL_CHECK(err, err = kernel_top.setArg(arg_id, buffer_r[i]));
		OCL_CHECK(err, err = kernel_top.setArg(arg_id + 1, buffer_w[i]));
		arg_id += 2;
	}
	
	// Copy input data to device global memory
	OCL_CHECK(err, err = q.enqueueMigrateMemObjects(buffer_r,0/* 0 means from host*/));

    if (debug) {
        s = high_resolution_clock::now();
    }
    
	// Launch the Kernel
	OCL_CHECK(err, err = q.enqueueTask(kernel_top));

	// Copy Result from Device Global Memory to Host Local Memory
	OCL_CHECK(err, err = q.enqueueMigrateMemObjects(buffer_w, CL_MIGRATE_MEM_OBJECT_HOST));

    OCL_CHECK(err, err = q.finish());
    
    if (debug) {
        diff = high_resolution_clock::now() - s;
    }
    
    for(int i=0;i < total_output_data;i++)
        output_data[i] = output[i];
    
     if (debug) {
        timeExec = diff.count();
        str_return += "Execution Time: " + std::to_string(timeExec * 1000) + "ms\n";
     }
    return str_return;
}






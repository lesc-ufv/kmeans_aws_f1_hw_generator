#include <stdio.h>
#include <stdlib.h>
#include <cstring>
#include <iostream>
#include <fstream>
#include <sstream>
#include <chrono>
#include <vector>
#include <string>

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

using namespace std;
using namespace std::chrono;

typedef  std::vector<char, aligned_allocator<char>> vector_u8;


int main(int argc, char **argv);

std::string kmeans_process(std::string binaryFile,bool debug, char *main_vector, int total_main_vector_bytes, char *output_data, int total_output_data);

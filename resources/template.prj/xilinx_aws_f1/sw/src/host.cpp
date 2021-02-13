#include "host.h"

int main(int argc, char **argv) {
    int num_points;
    int max_iterations;
    int num_clusters;
    int num_dims;
    std::string data_in_file_path;
    std::string output_file;
    std::string binaryFile;
    
    if (argc > 6) {
        binaryFile = argv[1];
        num_points = atoi(argv[2]);
        num_clusters = atoi(argv[3]);
        num_dims = atoi(argv[4]);
        max_iterations = atoi(argv[5]);
        data_in_file_path = argv[6];
        output_file = "./kmeans_" + std::to_string(num_points) + "_" + std::to_string(num_clusters) +
                      "_" + std::to_string(num_dims) + "_out_fpga" + ".txt";
    } else {
        std::cout << "invalid args!!!\n";
        std::cout << "usage: <xclbin> <num_points> <num_clusters> <num_dims> <max_iterations> <data_file>\n";
        exit(255);
    }
    
    KmeansFpga kmeans;
    kmeans.kmeans_fpga_init(binaryFile);
    kmeans.kmeans_allocate(num_points,num_clusters,num_dims);
    kmeans.read_file(data_in_file_path);
    kmeans.kmeans_clustering(max_iterations,output_file);
    kmeans.kmeans_deallocate();
    kmeans.kmeans_print_report();
    return 0;
    
}

# An Open Source Custom K-means Generator for AWS Cloud FPGA Accelerators

### Abstract:

Nowadays, FPGAs play an essential role in domain-specific hardware accelerators due to their power efficiency and flexibility. Nevertheless, FPGA programming and deploying are still a challenge. We present an accelerator generator targeting Amazon Web Services (AWS) Cloud FPGAs. We validate our generator with the K-means clustering algorithm as a case study. The main contribution of this work is to present an opensource full-stack generator using AWS EC2 F1 cloud FPGAs. Our framework is parameterizable and generates Verilog code for the entire design, including DDR memory and FPGA communication. Furthermore, we use a modular design approach, allowing extensions to address other applications. Compared to the Intel/Altera Harpv2 cloud FPGA, our AWS accelerator is on average twice faster for the K-means case study.

### Cite this:

```
@INPROCEEDINGS{9628301,
  author={Bragança, Lucas and Canesche, Michael and Penha, Jeronimo and Carvalho, Westerley and Comarela, Giovanni and Nacif, José Augusto M. and Ferreira, Ricardo},
  booktitle={2021 XI Brazilian Symposium on Computing Systems Engineering (SBESC)}, 
  title={An Open Source Custom K-means Generator for AWS Cloud FPGA Accelerators}, 
  year={2021},
  volume={},
  number={},
  pages={1-8},
  doi={10.1109/SBESC53686.2021.9628301}}
```

### Usage:
```
./bin/create_project  -N <Features> -K <Clusters> -c <Copies>  -p <Project Name>
```

### Dependencies

- [Python 3](https://www.python.org/downloads/)
- [Veriloggen](https://github.com/PyHDI/veriloggen)




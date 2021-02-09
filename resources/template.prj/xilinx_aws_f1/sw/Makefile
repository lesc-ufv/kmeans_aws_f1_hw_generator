
TARGET := hw_emu
DEVICE := $(AWS_PLATFORM)
HOST_ARCH = x86

CXXFLAGS += $(opencl_CXXFLAGS) -Wall -O0 -g -std=c++11
LDFLAGS += $(opencl_LDFLAGS)

CXXFLAGS += -I$(shell readlink -f ./include) -I$(shell readlink -f ./include/xcl2)
LDFLAGS += -lrt -lstdc++ 

CXXFLAGS += -fmessage-length=0

HOST_SRCS =$(shell find ./src/ -iname *.cpp)
HOST_HDRS =$(shell find ./include/ -iname *.cpp)

EMCONFIG_DIR=./emconfig_dir
EXECUTABLE =./kernel_top

SIM_XCLBIN=$(shell find ../hw/simulate -iname kernel_top.xclbin)
HW_XCLBIN=$(shell find ../hw/synthesis -iname kernel_top.awsxclbin)

.PHONY:first
first:host

include opencl.mk
include simconf.mk
include checks.mk

.PHONY: host
host: $(EXECUTABLE)

$(EXECUTABLE): check-xrt $(HOST_SRCS) $(HOST_HDRS)
	$(CXX) $(CXXFLAGS) $(HOST_SRCS) $(HOST_HDRS) -o '$@' $(LDFLAGS)

.PHONY: sim	
sim: host simconf emconfig
	XCL_EMULATION_MODE=$(TARGET) $(EXECUTABLE) $(SIM_XCLBIN) $(CGRA_BITSTREAM)

.PHONY: run
run: host
	$(EXECUTABLE) $(HW_XCLBIN) $(CGRA_BITSTREAM)

.PHONY: wave 
wave: sim
	xsim -gui *.wdb &
	
.PHONY:emconfig
emconfig: emconfig.json

emconfig.json:
	mkdir -p $(EMCONFIG_DIR)
	emconfigutil --platform $(DEVICE) --od $(EMCONFIG_DIR)
	cp $(EMCONFIG_DIR)/emconfig.json .

.PHONY: clean	
clean: 
	rm -rf $(EMCONFIG_DIR)
	rm -rf emconfig.json
	rm -rf $(EXECUTABLE)
	rm -rf xsim.tcl
	rm -rf xrt.ini
	rm -rf *.csv
	rm -rf *.link.*
	rm -rf *.log
	rm -rf *.jou
	rm -rf .ipcache
	rm -rf .Xil
	rm -rf xsim.dir
	rm -rf .hbs
	rm -rf .run

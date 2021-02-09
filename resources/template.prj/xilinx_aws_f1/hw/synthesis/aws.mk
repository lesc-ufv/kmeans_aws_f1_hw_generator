

create_vitis_afi=$(VITIS_DIR)/tools/create_vitis_afi.sh
BUCKET_NAME=my-bucket-fpga
FOLDER=$(shell cat ./prj_name)
LOGS=logs

.PHONY: aws
aws: $(BUILD_DIR)/kernel_top.awsxclbin

$(BUILD_DIR)/kernel_top.awsxclbin: $(BUILD_DIR)/kernel_top.xclbin
	touch FILES_GO_HERE.txt
	aws s3 mb s3://$(BUCKET_NAME)/$(FOLDER)
	aws s3 cp FILES_GO_HERE.txt s3://$(BUCKET_NAME)/$(FOLDER)/
	$(create_vitis_afi) -xclbin=$(BUILD_DIR)/kernel_top.xclbin -o=kernel_top -s3_bucket=$(BUCKET_NAME) -s3_dcp_key=$(FOLDER) -s3_logs_key=$(LOGS)

cleanaws:
	aws s3 rm s3://$(BUCKET_NAME)/$(FOLDER)/
	rm -rf to_aws
	rm -rf *.dcp *.txt *.tar *.awsxclbin *.json

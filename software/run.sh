#!/bin/bash

# Data Collection Script for Sparrow-Albatros System
# This script automates the process of mounting drives, configuring the FPGA,
# and starting data collection for both spectra and baseband data.

echo "Starting data collection process..."

# Step 1: Find the storage drive
echo "Listing block devices to identify storage drive..."
lsblk
DRIVE_NAME=$(lsblk -o NAME,SIZE,TYPE | grep -i "disk" | awk '{print $1}' | head -1)
PARTITION="${DRIVE_NAME}1"
echo "Detected drive: ${DRIVE_NAME}, partition: ${PARTITION}"

# Step 2: Mount the drive
echo "Mounting drive /dev/${PARTITION} to /media/BASEBAND..."
sudo mkdir -p /media/BASEBAND
sudo mount /dev/${PARTITION} /media/BASEBAND
if [ $? -ne 0 ]; then
    echo "Error mounting drive. Attempting with default sda1..."
    sudo mount /dev/sda1 /media/BASEBAND
    if [ $? -ne 0 ]; then
        echo "Failed to mount drive. Please check drive connection and try again."
        exit 1
    fi
fi
echo "Drive mounted successfully."

# Step 3: Navigate to software directory
echo "Navigating to software directory..."
cd ~/sparrow-albatros/software
if [ $? -ne 0 ]; then
    echo "Error: Could not find software directory at ~/sparrow-albatros/software"
    echo "Please check the path and try again."
    exit 1
fi

# Step 4: Prompt for config file edits
echo "Do you want to edit the config.ini file? (y/n)"
read edit_config
if [[ $edit_config == "y" || $edit_config == "Y" ]]; then
    ${EDITOR:-nano} config.ini
    echo "Configuration updated."
else
    echo "Using existing configuration."
fi

# Step 5: Configure the FPGA
echo "Configuring FPGA..."
python configfpga.py
if [ $? -ne 0 ]; then
    echo "Error configuring FPGA. Please check connections and try again."
    exit 1
fi
echo "FPGA configured successfully. Please verify that switch lights are flashing consistently."
echo "Waiting for confirmation to continue (press Enter when ready)..."
read -p ""

# Step 6 & 7: Start screen session for recording on-board correlations
echo "Starting screen session for spectral data collection..."
screen -dmS spec bash -c "cd ~/sparrow-albatros/software && python dump_spectra.py; exec bash"
echo "Screen session 'spec' started for spectral data collection."

# Step 9 & 10: Start screen session for baseband collection
echo "Starting screen session for baseband collection..."
screen -dmS baseband bash -c "cd ~/sparrow-albatros/software; exec bash"

# Wait 15 seconds before running set_optimal_coeffs.py
echo "Waiting 15 seconds before setting optimal coefficients..."
sleep 15

# Step 10: Set optimal coefficients for 4-bit data
echo "Do you want to collect 4-bit data? (y/n)"
read collect_4bit
if [[ $collect_4bit == "y" || $collect_4bit == "Y" ]]; then
    echo "Setting optimal coefficients for 4-bit data..."
    screen -S baseband -X stuff "python set_optimal_coeffs.py\n"
    sleep 5
fi

# Step 11: Compile the C code
echo "Compiling C code for baseband data collection..."
screen -S baseband -X stuff "make clean;make\n"
sleep 5

# Step 12: Run the C code with superuser privileges
echo "Running baseband data collection with sudo..."
screen -S baseband -X stuff "sudo ./dump_baseband\n"

# Step 14: Check that data is being collected
echo "Data collection started. Checking for file growth..."
echo "Checking spectral data files in ~/data_auto_cross:"
ls -lh ~/data_auto_cross/
echo "Checking baseband data files in /media/BASEBAND/baseband:"
ls -lh /media/BASEBAND/baseband/

# Setup a monitoring loop
echo "Monitoring file growth. Press Ctrl+C to exit monitoring (data collection will continue)."
counter=0
while [ $counter -lt 5 ]; do
    sleep 10
    echo "Updated spectral data files (~/data_auto_cross):"
    ls -lh ~/data_auto_cross/
    echo "Updated baseband data files (/media/BASEBAND/baseband):"
    ls -lh /media/BASEBAND/baseband/
    counter=$((counter+1))
done

echo "Data collection is running in screen sessions."
echo "To view spectral data collection: screen -r spec"
echo "To view baseband data collection: screen -r baseband"
echo "To detach from a screen session: Ctrl+A followed by D"
echo "Data collection script completed successfully."


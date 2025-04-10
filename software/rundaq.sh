#!/bin/bash

echo "This script will configure the fpga, run dump_baseband and dump_spec.py. Make sure that a drive is mounted and that config.ini is configured the way you want it before you proceed. Run this script in sudo."

# Get python interpreter path
PYTHON_PATH=/home/casper/python3-venv/bin/python

# cd into the DAQ software directory
DAQ_PATH="/home/casper/sparrow-albatros/software"
cd $DAQ_PATH
echo pwd

# Set the system clock
$PYTHON_PATH set_gps_clock.py

# Default config file
CONFIG_FILE="config.ini"

# Parse command line arguments
while getopts "c:" opt; do
    case $opt in 
        c)
            CONFIG_FILE="$OPTARG"
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            exit 1
            ;;
    esac
done

echo "Using config file: $CONFIG_FILE"

# Run FPGA configuration
echo "\nRunning configfpga.py with config file ${CONFIG_FILE}"
$PYTHON_PATH configfpga.py -c $CONFIG_FILE

echo "\nWaiting 10 seconds for spectra to accumulate..."
sleep 10 
echo "done waiting, now running dump_spectra.py and dump_baseband"

# Create and detach from spectra screen session
screen -dmS spec sudo $PYTHON_PATH dump_spectra.py
echo "screen: dumpm spectra launched"
 
# Create baseband screen session
screen -dmS baseband bash -c "$PYTHON_PATH set_optimal_coeffs.py && sleep 1 && sudo ./dump_baseband"
echo "screen: dump baseband launched"

#$PYTHON_PATH set_optimal_coeffs.py
#sleep 1
#sudo ./dump_baseband

echo "Done! Sessions running in background."

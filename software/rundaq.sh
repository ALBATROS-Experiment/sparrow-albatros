#!/bin/bash

# Get python interpreter path
PYTHON_PATH=/home/casper/python3-venv/bin/python

# Set the system clock
$PYTHON_PATH set_gps_clock.py

echo "This script will configure the fpga, run dump_baseband and dump_spec.py. Make sure that a drive is mounted and that config.ini is configured the way you want it before you proceed."

read -p "Press Enter to continue..."

# Run FPGA configuration
$PYTHON_PATH configfpga.py
echo "configfpga.py executed"

echo "Waiting 10 seconds for spectra to accumulate"
sleep 10 

# Create and detach from spectra screen session
screen -dmS spec sudo $PYTHON_PATH dump_spectra.py
echo "screen: dumpm spectra launched"

# Create baseband screen session
screen -dmS baseband bash -c "$PYTHON_PATH set_optimal_coeffs.py && sleep 1 && sudo ./dump_baseband"
echo "screen: dump baseband launched"

echo "Done! Sessions running in background."

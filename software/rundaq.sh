#!/bin/bash

echo "This script will configure the fpga, run dump_baseband and dump_spec.py. Make sure that a drive is mounted and that config.ini is configured the way you want it before you proceed. Also, don't run this in sudo."

read -p "Press Enter to continue..."

# Get current python executable
PYTHON_PATH=$(which python)

# Set the system clock
$PYTHON_PATH set_gps_clock.py

# Run FPGA configuration
$PYTHON_PATH configfpga.py

# Create and detach from spectra screen session
screen -dmS spec sudo $PYTHON_PATH dump_spectra.py

# Create baseband screen session
screen -dmS baseband bash -c "sleep 10 && $PYTHON_PATH set_optimal_coeffs.py && sleep 1 && sudo ./dump_baseband"

echo "Done! Sessions running in background."

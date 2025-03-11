# sparrow-albatros
A repository for ALBATROS FPGA firmware (aka gateware) and embedded software targetting the Sparrow FPGA board. The embedded software runs on the Sparrow's ARM core. The gateware is designed to run on the Sparrow's FPGA. The Sparrow's ARM core boots a lightweight Ubuntu distribution from an SD card; this repository uses git-lfs to checkpoint images of the SD card.

Documentation documents
- [TODO] Running the data aquisition system (most basic use cases of a functioning system)
- [TODO] Running the data aquisition system (under the hood)
- [TODO] Data acquisition hardware
- [TODO] Setup an SD card with the data aquisition software
- [TODO] Embedded software detailed documentation (dev)
- [TODO] FPGA gateware logic overview 
- [TODO] FPGA gateware--setting up the toolchain and synthesising gateware


## Embedded software
xyz

## Gateware
### Software Versions:
- Ubuntu 20.04
- Xilinx Vivado System Edition 2021.2
- MATLAB/Simulink 2021a

### To open/modify/compile:

1. Clone this repository
2. Clone submodules:
```
git submodule update --init --recursive
```
3. Create a local environment specification file `firmware/startsg.local`.
4. From `firmware/`, run `startsg` (if your environment file is called `startsg.local`) or `startsg <my_local_environment_file.local>`.

### Repository Layout

 - `firmware/` -- Firmware source files and libraries
 - `software/` -- Libraries providing communication to FPGA hardware and firmware
 - `docs/` -- Documentation

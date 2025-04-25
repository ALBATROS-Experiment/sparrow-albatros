# Sparrow Albatros 

This repository serves three purpouses. The first is to house and version control **embedded software** that runs on the Sparrow's ARM's processor. The second is to house and version control **gateware** that runs on the Sparrow's FPGA. The third is to store and checkpoint **disk-images** of the OS that run the data acquisition software. The embedded software mates with the gateware, so it's conveniant to track them in the same repository. 

## Embedded software

We're running Ubuntu18 on the on the Zynq's ARM core. The software that runs on this processor loads and configures gateware to the FPGA, controls peripheral devices (such as mounting external storage), and runs data acquisition jobs (such as routing and re-packaging UDP packets' payloads (binary data) to files to external storage). This software can be found in the /software directory. Everything in this repository that runs on the ARM core comes from this directory. 

## Gateware

The digital signal processing logic, or 'gateware', runs on the Sparrow's Zync xc7z-series FPGA. The gateware implements all our real-time digital signal processing. Zync xc7z-series chips comprise a dual core ARM Cortex-A9 processor, programable FPGA fabric, and two configuratble ADCs.


## Disk Images

Disk images of the Ubuntu18 operating system and file-system running on the ARM core are tracked in this repository. We use git-lfs and exclude them from downloading by default as they are each about 2GB large. By tracking disk images here we can recreate a bit-accurate release of sparrow-albatros without *relying on anything outside of this repository*.



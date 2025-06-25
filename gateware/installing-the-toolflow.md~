# CASPER Toolflow

:warning: The toolflow *will not work* if it is installed on a version of Ubuntu that's not supported. For the latest official CASPER toolflow installation guide visit [the CASPER tutorial docs](https://casper-toolflow.readthedocs.io/en/latest/src/Installing-the-Toolflow.html). It's safest to assume you must abide every version and subversion and installation detail *by the letter*.

Although we ended up using CASPER virtual machine for compiles, which means we ultimately didn't use the natively instlaled toolchain, we here briefly summarize [the hurdles we came upon during native installation](https://gist.github.com/dcxSt/13f0760ee423082f15e151170b943fa6). You will notice that I failed to heed CASPER's warning advice and tried to install the toolflow on the wrong version of Ubuntu (22.04 instead of 20.04). 

## Introduction 

This section documents the installation and configuration of the CASPER toolflow on Ubuntu 22.04.1, specifically addressing the integration challenges between MATLAB R2021a, Xilinx Vivado 2021.1, and the CASPER development environment. While the CASPER developers have indicated that this specific combination of software versions is unsupported and can cause simulation failures in Simulink, this guide provides (some) solutions to the critical compatibility issues encountered during installation.

## System Perparation

The installation begins with a fresh Ubuntu 22.04.1 installation on an SSD. After creating a user account and connecting to the network for updates, several essential tools need to be installed. The system requires SSH server capabilities for remote access, which can be configured with custom port settings and public key authentication for enhanced security. Git and Git LFS are essential for managing the CASPER repository and its large files.

Additional system utilities such as htop, vim, and net-tools provide necessary system monitoring and network configuration capabilities. The net-tools package is particularly important as it provides the ifconfig command required for network interface management.

## Vivado 2022.2 Installation Process

The installation of Vivado 2022.2 requires downloading the web installer from Xilinx's official download portal. Before proceeding with the installation, several system dependencies must be addressed to prevent installation failures. The critical dependencies are libtinfo5, libncurses5, libcanberra-gtk-module, and libcanberra-gtk3-module. Without these packages, the installation process typically stalls during the "Generating installed devices list" phase, and the completed installation may experience display issues where labels fail to render in schematics and device cells.

After installing these dependencies, the Vivado installer can be executed with appropriate permissions. The installation process includes selecting Vitis and enabling the Vitis IP cache. The download and installation process typically requires approximately two hours, with the full installation consuming 83 GB of disk space.

## Vivado 2021.1 Installation

The installation process for Vivado 2021.1 follows the same procedure as version 2022.2, requiring the same system dependencies. Both versions can coexist on the same system, which can be useful for compatibility testing with different CASPER toolflow versions.

## Vivado Licence Configuration

Vivado requires a valid license for synthesis and implementation. The license manager, accessible through the Help menu in Vivado, facilitates the connection to Xilinx's licensing server. A node-locked license must be generated using the system's network interface MAC address. Once downloaded, the license file can be loaded through the license manager interface.

## MATLAB Installation

MATLAB R2021a installation follows a straightforward process using the installation media downloaded from MathWorks. The installation requires valid credentials and selection of an appropriate license. For the CASPER toolflow, the essential components include MATLAB base, Simulink, and the Signal Processing Toolbox. The installation directory should be set to a system-wide accessible location, typically /tools, with symbolic links created in /usr/local/bin for command-line access.

## Python Environment Setup

The CASPER toolflow requires Python 3.8, as newer versions may introduce compatibility issues. Ubuntu 22.04 ships with Python 3.10 by default, necessitating the installation of Python 3.8 through the deadsnakes PPA repository. A virtual environment should be created specifically for CASPER development to isolate dependencies and prevent conflicts with system packages.

The virtual environment requires python3.8-venv for creation and pip for package management. Essential build tools including build-essential and python3.8-dev must be installed to support the compilation of Python packages with C extensions.

## CASPER Toolflow Configuration

The CASPER mlib_devel repository should be cloned from the official GitHub repository, specifically the m2021a branch for compatibility with MATLAB R2021a. The repository includes a requirements.txt file that specifies all necessary Python dependencies, which can be installed within the activated virtual environment.

Configuration involves copying the startsg.local.example file to startsg.local and modifying it to reflect the correct installation paths for MATLAB, Vivado, and the Python virtual environment. These paths must be absolute and correctly point to the installation directories established in previous steps.

## Library Conflict Problem

A significant compatibility issue arises when launching MATLAB through the CASPER startsg script. The error manifests as a failure to load Simulink's built-in implementation library, specifically citing an undefined symbol `__gmpn_cnd_sub_n` in the system's libhogweed.so.6 library. This error prevents Simulink from functioning properly, with the GUI failing to display tool tabs and rendering the environment unusable for CASPER development.

Investigation reveals that this issue stems from a library conflict between Xilinx's bundled version of libgmp.so.10 and the system's version. The Xilinx versions of this library, distributed with both Vivado and Model Composer, fail to define certain symbols required by Ubuntu's cryptographic libraries, which Simulink depends on for its GUI functionality.

The resolution involves replacing all instances of Xilinx's libgmp.so.10 with the system's version. This requires locating all copies of the library within the Xilinx installation directory using a recursive find command. Typically, at least two instances exist: one in the Vivado subdirectory and another in the Model Composer subdirectory.

Rather than deleting Xilinx's versions, which might be needed for debugging or rollback purposes, they should be moved to a subdirectory named 'exclude'. The system's version of libgmp.so.10, located at /lib/x86_64-linux-gnu/libgmp.so.10, should then be copied to replace each instance.

This solution addresses the symbol resolution issue while maintaining the ability to restore the original configuration if needed. After implementing this fix, the CASPER toolflow can be launched successfully using the startsg script, with full Simulink functionality restored.

## Verification and Testing

Successful installation can be verified by launching the toolflow by executing the ./startsg bash script from the mlib_devel directory. Simulink should open with full GUI functionality, and CASPER library blocks should be accessible and configurable. A simple test involves creating a model with CASPER blocks such as an FFT, setting parameters, and confirming that no xbsIndex_r4 errors occur.

## Additional Considerations

For systems with mixed performance cores, such as those with both P-cores and E-cores, process affinity can be managed using taskset to ensure Vivado synthesis and implementation processes utilize the faster cores. Remote desktop access can be configured using either the native Ubuntu remote desktop functionality or xrdp for enhanced flexibility.

## Concluding Remarks

We were able to compile firmware with this toolflow and fixes but not take advantage of Simulink's digital design simulation functionality. Ultimately we switched to CASPER's Virtual Machine. My reccomendation to you is that you use exactly the OS specified in the [CASPER guide](https://casper-toolflow.readthedocs.io/en/latest/src/Installing-the-Toolflow.html). 










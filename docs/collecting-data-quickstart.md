
We start from the assumption that you have correctly setup the Sparrow-Albatros readout system.

## Boot and tunnel into the Sparrow
1. Power the RF-shielded box with a 24V power supply through the barrel port labelled IN. The Zynq's ARM core will boot off of the SD card mounted in the Sparrow's SD card slot. 
2. Connect your laptop to the Sparrow using an ethernet cable. 
3. If you have trouble with the next two steps you may need to configure the ethernet interface manually to be on the 10.10.xx.xx subnet (subnet mask 255.255.0.0, with an IP address e.g. 10.10.11.55)
4. Check that you can connect to the Sparrow with `ping 10.10.11.99`. The Sparrow's IP address on this LAN is set statically and should not change. Then ssh into the Sparrow with `ssh casper@10.10.11.99`. When prompted


## Collecting data
Now that you've tunneled in, you can run data collection. 

1. Find out the name of the drive connected with `lsblk`, it will probably be `sda1`
2. Mount the drive `sudo mount /dev/sda1 /media/BASEBAND`
3. Navigate to the software directory `cd ~/sparrow-albatros/software`
4. Modify the user configuration file `config.ini` to fit your needs
5. Configure the FPGA with `python configfpga.py` and make sure the switch's lights are flashing consistently. 
6. Start a screen session for recording the on board correlations `screen -S spec`
7. From this screen session run `python dump_spectra.py`. You may need to run this in sudo in which case make sure to run the correct python interpreter. Find the one activated in the current VM with `which python`, then copy the result of this and run `sudo </path/to/python/interpreter> dump_spectra.py`
8. Detach yourself from the screen session with `ctrl`+`a`+`d` 
9. Start a new screen session for running the baseband collection script `screen -S baseband`
10. If you are collecting 4-bit data run `python set_optimal_coeffs.py`, this uses the on board correlation to optimally set the digital gain coefficients at the requantization stage. [!NOTE] This can only be run at least 15 seconds after the FPGA has been configured (step 5)
11. Compile the c-code that reads UDP packets and writes them to disk with `make clean;make`
12. Run the c-code with superuser privilages `sudo ./dump_baseband`
13. Detach yourself from the screen session `ctrl`+`a`+`d`
14. Check that on-board correlations are being written to `~/data_auto_cross` and that baseband is being written to `/media/BASEBAND/baseband`. An easy way to do this is to `ls -lh` multiple times and watch files grow.




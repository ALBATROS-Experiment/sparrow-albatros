
Started from a booted Saprrow system. 

1. Boot the Sparrow system box, connect the ethernet port to your laptop with an ethernet cable (RJ45 connector, you'll need an ethernet port or dongle for your laptop)
2. The Sparrow's ARM is configured to statically assign it's Eth0 interface to the `10.10.11.99` ipv4 address. If you have trouble with the next two step you may need to configure the ethernet interface manually to be on the 10.10.xx.xx subnet (subnet mask 255.255.0.0, with an IP address e.g. 10.10.11.55)
3. Mount a hard drive connected over usbA port to this mountpoint: `/media/BASEBAND` with this command `sudo mount /dev/<your HD partition e.g. sda2> /media/BASEBAND`
    - run `lsblk` to identify connected hard drives (Sparrow only supports ext4 formated hard drives)
4. In your terminal, enter the data acquisition directory using the aliased shortcut `daq` (you should now have cd'd into `/home/casper/sparrow-albatros/software`)
5. Adjust the `config.ini` configuration file to suit your needs
6. Run the DAQ in sudo by executing `sudo ./rundaq`
7. Make sure that baseband is being written 



## Boot and tunnel into the Sparrow
1. Power the RF-shielded box with a 24V power supply through the barrel port labelled IN. The Zynq's ARM core will boot off of the SD card mounted in the Sparrow's SD card slot. 
2. Connect your laptop to the Sparrow using an ethernet cable. 
4. Check that you can see the Sparrow on the network with `ping 10.10.11.99`. The Sparrow's IP address on this LAN is set statically and should not change. Then ssh into the Sparrow with `ssh casper@10.10.11.99`. Enter the password `casper` when prompted. 


## Collecting data getting started manually
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
14. Check that on-board correlations are being written to `~/data_auto_cross` and that baseband is being written to `/media/BASEBAND/baseband`. An easy way to do this is to `ls -lh` multiple times and watch files grow. Make sure the baseband is sensible (not all zeros or railed) by sniffing the packets and looking at hexdumps of the payloads with Wireshark. 




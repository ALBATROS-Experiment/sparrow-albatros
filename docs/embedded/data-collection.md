# Collecting data

## Quick start

1. **Power and boot** the Sparrow system box, connect the ethernet port to your laptop with an ethernet cable (RJ45 connector, you'll need an ethernet port or dongle for your laptop)
2. **SSH** into the Ubuntu OS running on the Sparrow's ARM core with `ssh casper@10.10.11.99`, enter the password, "casper", when prompted. The Sparrow's ARM is configured to statically assign it's Eth0 interface to the `10.10.11.99` ipv4 address. If you have trouble with the next two steps you may need to configure your laptop's wired ethernet interface manually to be on the 10.10.xx.xx subnet (subnet mask 255.255.0.0, with an IP address e.g. 10.10.11.55)
3. **Mount a hard drive** connected over usbA port to this mountpoint: `/media/BASEBAND` with this command `sudo mount /dev/<your HD partition e.g. sda2> /media/BASEBAND`. Then run `lsblk` to identify connected hard drives (only ext4 formated hard drives are supported). Make sure that the HDD's mounted partition has a `/baseband` subdirectory in its root directory. If not, create one.
4. Enter the data acquisition directory using the aliased shortcut `daq` (you should now have cd'd into `/home/casper/sparrow-albatros/software`).
5. Edit the `config.ini` configuration file to suit your needs.
6. Run the DAQ in sudo by executing `sudo ./rundaq.sh`.

That's it! 

## Checking and troubleshooting

- Verify that baseband is writing to `/media/BASEBAND/baseband`, that on-board-correlated data is writing to `/home/casper/data_auto_cross`, and that logs are writing to `/home/casper/logs`. 
- If baseband is not writing, open up Wireshark on your laptop and snoop on your wired connection in promiscuous mode. If baseband is dumping correctly you'll be met with a deluge of UDP packets. Look at one of those UDP packets and make sure the UDP payload is not all zeros. You should be weary if there are too many zeros, the data is almost incompressible (i.e. very high entropy).  
- To verify the integrity of your signal, use -X port forwarding and run `python livespec.py 0 125` (in the `daq` directory). 

## In Depth
If you're going to modify the code it's good to know how it all sticks together. 


---

TODO: everything below here needs to be deleted/adapted to explain what rundaq.sh does instead

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


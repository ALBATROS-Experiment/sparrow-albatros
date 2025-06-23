# Collecting data

## Quick start

1. **Power and boot** the Sparrow system box, connect the ethernet port to your laptop with an ethernet cable (RJ45 connector, you'll need an ethernet port or dongle for your laptop)
2. **SSH** into the Ubuntu OS running on the Sparrow's ARM core with `ssh casper@10.10.11.99`, enter the password, "casper", when prompted. The Sparrow's ARM is configured to statically assign it's Eth0 interface to the `10.10.11.99` ipv4 address. If you have trouble with the next two steps you may need to configure your laptop's wired ethernet interface manually to be on the 10.10.xx.xx subnet (subnet mask 255.255.0.0, with an IP address e.g. 10.10.11.55)
3. **Mount a hard drive** connected over usbA port to this mountpoint: `/media/BASEBAND` with this command `sudo mount /dev/<your HD partition e.g. sda2> /media/BASEBAND`. Then execute `lsblk` to identify connected hard drives (only ext4 formated hard drives are supported). Make sure that the HDD's mounted partition has a `/baseband` subdirectory in its root directory. If not, create one.
4. Change directory to the data acquisition directory using the aliased shortcut `daq` (you should now be in `/home/casper/sparrow-albatros/software`). 
5. Edit the `config.ini` configuration file to suit your needs.
6. Run the DAQ in sudo by executing `sudo ./rundaq.sh`.

That's it! 

## Quality Control (!)

First, sanity checks. 

<details>
<summary>
Sanity check the terminal output. A successful execution looks something like this
</summary>

```
sudo ./rundaq.sh 
[sudo] password for casper: 
This script will configure the fpga, run dump_baseband and dump_spec.py. Make sure that a drive is mounted and that config.ini is configured the way you want it before you proceed. Run this script in sudo.
cd into daq
pwd
GPS time is before 2025 and so is not to be believed.  Ignoring.
Failed to set system clock from GPS
Using config file: config.ini
cp: 'config.ini' and 'config.ini' are the same file

Running configfpga.py with config file config.ini
GPS time is before 2025 and so is not to be believed.  Ignoring.
Failed to set system clock from GPS
Parsing config.ini for relevant values
chans [ 500  500  501  501  502  502  503  503  504  504  505  505  506  506
  507  507  508  508  509  509  510  510  511  511  512  512  513  513
  514  514  515  515  516  516  517  517  518  518  519  519  520  520
  521  521  522  522  523  523  524  524  525  525  526  526  527  527
  528  528  529  529  530  530  531  531  532  532  533  533  534  534
  535  535  536  536  537  537  538  538  539  539  540  540  541  541
  542  542  543  543  544  544  545  545  546  546  547  547  548  548
  549  549  550  550  551  551  552  552  553  553  554  554  555  555
  556  556  557  557  558  558  559  559  560  560  561  561  562  562
  563  563  564  564  565  565  566  566  567  567  568  568  569  569
  570  570  571  571  572  572  573  573  574  574  575  575  576  576
  577  577  578  578  579  579 1836 1836 1837 1837 1838 1838 1839 1839
 1840 1840 1841 1841 1842 1842 1843 1843 1844 1844 1845 1845]
Spec per packet: 7
Bytes per spectrum: 180
Writing bitstream to FPGA and initializing...
Programming FPGA
INT 160
MOD 2
FRAC 0
output_divider 16
Estimated FPGA clock is 125.36
Initializing ADCs
Setting four bit coeffs.
FPGA clock: 125.36
Set FFT shift schedule to 1111111111111111
Set correlator accumulation length to 131072
Reset GBE (UDP packetizer)
Set spectra-per-packet to 7
Set bytes-per-spectrum to 180
Set quantization bit mode to 4-bits
NOT YET IMPLEMENTED: Setting destination MAC address to 0
Set destination IP address and port to 10.10.11.99:7417
Resetting packetizer
Resetting acc control and syncing
Sending pulse
No FFT overflows detected
Enabling 1 GbE output
No GbE overflows detected
Setup and tuning complete

Waiting 10 seconds for spectra to accumulate...
done waiting, now running dump_spectra.py and dump_baseband
screen: dump spectra launched
screen: dump baseband launched
Done! Sessions running in background.
```
</details>


<details>
<summary>
Sanity check your signal.
</summary>
<br>
To verify the integrity of your signal, use -X port forwarding and run `python livespec.py 0 125` (in the "daq" directory, `~/sparrow_albatros/software`).

[img placeholder]

<br/><br/>
</details>


<br/>
Next, verify that baseband is writing to `/media/BASEBAND/baseband`, that on-board-correlated data is writing to `/home/casper/data_auto_cross`, and that logs are writing to `/home/casper/logs`. 


<details><summary>Check on baseband process</summary>
```
$ ps aux | grep baseband
root      3235  0.0  0.1   5012  1740 ?        Ss   14:53   0:00 SCREEN -dmS baseband bash -c /home/casper/python3-venv/bin/python set_optimal_coeffs.py && sleep 20 && sudo ./dump_baseband
root      3237  0.0  0.2   7108  2856 pts/2    Ss+  14:53   0:00 sudo ./dump_baseband
root      3321 28.4  4.1  51424 42432 pts/2    S+   14:53   0:47 ./dump_baseband
casper    3414  0.0  0.0   3852   492 pts/1    S+   14:56   0:00 grep --color=auto baseband
```

If baseband is not writing, open up Wireshark on your laptop and snoop on your wired connection in promiscuous mode. If baseband is dumping correctly you'll be met with a deluge of UDP packets. Look at one of those UDP packets and make sure the UDP payload is not all zeros. You should be weary if there are too many zeros, the data is almost incompressible (very high entropy).<br><br>
</details>

<details>
<summary>Check on spec process</summary>
```
$ ps aux | grep spec
root      3232  0.0  0.1   5012  1772 ?        Ss   14:53   0:00 SCREEN -dmS spec sudo /home/casper/python3-venv/bin/python dump_spectra.py
root      3234  0.0  0.2   7108  2828 pts/0    Ss+  14:53   0:00 sudo /home/casper/python3-venv/bin/python dump_spectra.py
root      3254 51.0  3.4  61624 35300 pts/0    Rl+  14:53   2:00 /home/casper/python3-venv/bin/python dump_spectra.py
casper    3534  0.0  0.0   3852   492 pts/1    S+   14:57   0:00 grep --color=auto spec
```
</details>

<details>
<summary>Confirm baseband is writing to disk. Note that if you're writing at a low datarate it may take a while for data to start writing as it's buffered and written to disk in 20M chunks.</summary> 
```
$ ls -lh /media/BASEBAND/baseband/17506
-rw-r--r-- 1 root root 218M Jun 23 14:58 1750690667.raw
$ ls -lh /media/BASEBAND/baseband/17506
-rw-r--r-- 1 root root 240M Jun 23 14:58 1750690667.raw
$ ls -lh /media/BASEBAND/baseband/17506
-rw-r--r-- 1 root root 300M Jun 23 14:58 1750690667.raw
```
</details>

<details>
<summary>Confirm that spectra are being dumped to `/home/casper/data_auto_cross`</summary>
```
$ ls -lh /home/casper/data_auto_cross/17506/1750694151
-rw-r--r-- 1 root root 4.5K Jun 23 16:34 acc_cnt1.raw
-rw-r--r-- 1 root root 4.5K Jun 23 16:34 acc_cnt2.raw
-rw-r--r-- 1 root root  18M Jun 23 16:34 adc0.scio
-rw-r--r-- 1 root root  18M Jun 23 16:34 adc1.scio
-rw-r--r-- 1 root root 4.5K Jun 23 16:34 adc_temp.raw
-rw-r--r-- 1 root root 4.5K Jun 23 16:34 fft_of_count1.raw
-rw-r--r-- 1 root root 4.5K Jun 23 16:34 fft_of_count2.raw
-rw-r--r-- 1 root root  18M Jun 23 16:34 pol00.scio
-rw-r--r-- 1 root root  18M Jun 23 16:34 pol01i.scio
-rw-r--r-- 1 root root  18M Jun 23 16:34 pol01r.scio
-rw-r--r-- 1 root root  18M Jun 23 16:34 pol11.scio
-rw-r--r-- 1 root root 4.5K Jun 23 16:34 time_gps_start.raw
-rw-r--r-- 1 root root 4.5K Jun 23 16:34 time_gps_stop.raw
-rw-r--r-- 1 root root 9.0K Jun 23 16:34 time_sys_start.raw
-rw-r--r-- 1 root root 9.0K Jun 23 16:34 time_sys_stop.raw
$ ls -lh /home/casper/data_auto_cross/17506/1750694151
-rw-r--r-- 1 root root 4.6K Jun 23 16:34 acc_cnt1.raw
-rw-r--r-- 1 root root 4.6K Jun 23 16:34 acc_cnt2.raw
-rw-r--r-- 1 root root  19M Jun 23 16:34 adc0.scio
-rw-r--r-- 1 root root  19M Jun 23 16:34 adc1.scio
-rw-r--r-- 1 root root 4.6K Jun 23 16:34 adc_temp.raw
-rw-r--r-- 1 root root 4.6K Jun 23 16:34 fft_of_count1.raw
-rw-r--r-- 1 root root 4.6K Jun 23 16:34 fft_of_count2.raw
-rw-r--r-- 1 root root  19M Jun 23 16:34 pol00.scio
-rw-r--r-- 1 root root  19M Jun 23 16:34 pol01i.scio
-rw-r--r-- 1 root root  19M Jun 23 16:34 pol01r.scio
-rw-r--r-- 1 root root  19M Jun 23 16:34 pol11.scio
-rw-r--r-- 1 root root 4.6K Jun 23 16:34 time_gps_start.raw
-rw-r--r-- 1 root root 4.6K Jun 23 16:34 time_gps_stop.raw
-rw-r--r-- 1 root root 9.1K Jun 23 16:34 time_sys_start.raw
-rw-r--r-- 1 root root 9.1K Jun 23 16:34 time_sys_stop.raw
```
</details>
<br/>

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


# Networking

SFP0 (FPGA) <--> Eth0 (ARM)
Eth0 (ARM) <--> External connection (laptop)
Eth0 (ARM) <--> External connection (Starlink)

Our Swtich handles this. 

## Network Configuration on the ARM

- hardware constraints (it only has an Eth0 port 1GBE, no wifi NIC+antenna, no second Eth driver)
- known issues 
    - if you're running an -X session without compression expect dropped packets
- ifconfig


Modified packetizer/four-bit-reorder data/clock delays to compensate for pulse-data missallignment. There was an off-by-two error in the 4bit reorder logic compensated for by the packetizer, both were corrected even though the packetizer data delay patch isn't fully understood. This was caught because the 1bit logic was simulating aligned but off by two bytes on the FPGA--caused by the packetizer off-by-two. 

### Packetizer

High level schematic of packetizer with gpio on downstream and re-quantizer muxes upstream

![image](https://github.com/user-attachments/assets/b22b1e6b-3053-4ccc-a184-15a4209d392a)

Extra delay fudge factor delay added to data line to compensate for alignment bug of unknown origin

![image](https://github.com/user-attachments/assets/e2a91e00-5227-4efd-9f3b-5c4ef2f3e6df)


### 4-bit reorder

High level schematic to place 4-bit reorder in context

![image](https://github.com/user-attachments/assets/30c9ce6f-8032-4c9a-b759-7da6e5fd9e81)

Corrected delays, from z-1 to z-3. This is linked to a bug in one of the casper BRAM blocks that resets itsself to z-3 when you set it to z-1. 

![image](https://github.com/user-attachments/assets/1feb45c2-7efa-4900-b5a4-a98572385a6d)


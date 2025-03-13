Modified packetizer/four-bit-reorder data/clock delays to compensate for pulse-data missallignment. There was an off-by-two error in the 4bit reorder logic compensated for by the packetizer, both were corrected even though the packetizer data delay patch isn't fully understood. This was caught because the 1bit logic was simulating aligned but off by two bytes on the FPGA--caused by the packetizer off-by-two. 

### Packetizer

High level schematic of packetizer with gpio on downstream and re-quantizer muxes upstream

[img]

Extra delay fudge factor delay added to data line to compensate for alignment bug of unknown origin

[img]


### 4-bit reorder

High level schematic to place 4-bit reorder in context

[img]

Corrected delays, from z-1 to z-3. This is linked to a bug in one of the casper BRAM blocks that resets itsself to z-3 when you set it to z-1. 

[img]


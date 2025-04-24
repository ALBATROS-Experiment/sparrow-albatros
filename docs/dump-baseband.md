# Dumping Baseband

## User guide

Remember, baseband is quantized, "raw" (uncorrelated), Fourier domain data. After quantization and packetization, the FPGA streams baseband UDP packets on a 1GBE link from SFP port 0 to a small switch packaged up with the box. A `dump_baseband` process running on the ARM core recieves these packets, and buffer-writes them to files on the HDD. 

The `dump_baseband.c` xyz

## Under the hood 

The sparrow has four, 10GBE SFP ports but when used in 1GBE mode only port 0 is supported by the CASPER framework. 

## Benchmarks

- Throughput achievable (until packets are dropped?)
- How much of which resources are taken
    - RAM
    - CPU
- Pin to a core vs not pin to a core? 



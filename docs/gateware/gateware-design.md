# Gateware Design Overview
The digital signal processing logic starts at the ADCs, gets PFB'd (Filter + FFT), then splits into two signal paths:

1. On board auto and cross correlations which can be read by the ARM core over SPI.
2. The logic re-quantizes the signal to 1 or 4 bits then selects and packages a subset of frequency channels into UDP packets which are streamed out of the Sparrow's 0'th SFP port. 

```
                                     _--> Correlator -> Readable BRAM (SPI)
2x Analog Signal -> ADC -> PFB/FFT _/
                                    \_--> 1bit quant |mux\_--> UDP Packets (1GBE)
                                      --> 4bit quant |   /
```

## Foreword on the Simulink-CASPER gateware design paradigm
The Simulink (Matlab) and CASPER framework abstracts away the nitty gritty plumbing inherent to modern (2025) FPGA programming in regular text-based HDLs. There are good, bad, and ugly things about this. 

The good: the user can jump right in and design, simulate, compile, implement, and synthesise a basic design targeted for supported hardware. The simulation aspect is worth emphasising because it's very easy to write a bug into logic design and it's often very hard to catch it without simulation. 

The bad: it is impossible to track small diffs with modern version control tools (git) between two commits because the .slx files, being diagramatic rather than text based, are big and stored in compressed binary format. 

The ugly side is that [the toolchain](installing-the-toolchain.md) is very brittle and annoying to set up. You need a precise Ubuntu distribution, which means you can't just set it up on any linux machine without reinstalling the operating system and migrating all users to that new OS. Not to mention that you need to buy, install, set up and periodically renew licences for bulky (~300 GB), propriotary Xilinx (AMD) software (Vivado) and Matlab's Simulink software. 

Once you have the toolchain running and are ready to assemble your first design, you'll notice that there are many different types of color-coded block. 

- The yellow (CASPER) blocks are IO bocks. They map hardware pins to logic, define user programmable BRAMS and registers
- The green (CASPER) blocks are (vaguely) DSP blocks. They implement logic to manipulate data. 
- The blue Xilinx blocks mix memory access and logic and are provided by Xilinx. These are primitive blocks provided by Xilinx, like operators or primitive data types in C.
- Some white blocks implement simulation-only logic and tools to help develop and simulate the gateware.
- The glossy grey blocks are user-defined *subsystems* that abstract away complexity, like a function in C or Python. Some white blocks also abstract user-defined logic, but these ones have 'mask parameters'. The values of mask parameters are set by the user before compilation, just like C macro-definitions. You can create one by highlighting some logic, righ-clicking, and selecting 'create subsystem from selection'. You can then turn a subsystem into a block with mask parameters by right-clicking the subsystem then Mask > Create Mask.

## ADC interface
The ADC interface block, labelled `sparrow_adc`, provides the plumbing to link the ADCs' output pins with the design. The `sync_adc` register provides an interface for the python framework to sync the ADCs. The ADCs are programmed to sample at 250 MSPS but the fabric clock in this design is configured to run at 125 MSPS. To accomplish this clock domain crossing ADC samples are loaded into the fabric two at a time from each Pol (analog channel). The four output pins labels `data_a/b_0/1` denote a/b for pol0/1 and 0/1 for first and second samples within one fabric-clock period.
![image](https://github.com/user-attachments/assets/87739643-ff36-4363-bd93-22c0d8739f6b)


## PFB FIR 
The Polyphase Filter Bank Finite Impulse Response stage comprises four (number of inputs) sets of a series of four (number of taps) shift registers. Four frames worth of data from each ADC is windowed (point-wise multiplied by a vector of 'window coefficients'), then stacked and summed vertically. The output of this FIR filter feeds into the FFT. Each frame is 4096 (2^12) samples wide.
![image](https://github.com/user-attachments/assets/ac2e2d48-125d-45a5-8674-a8d59bbc0b28)

The `sync` register is a user-writeable register which creates a 'sync pulse'. The sync pulse serves to align frames output by the PFB FIR filter with all of the logic downstream of it. This digital signal chain comprises an infinite loop of the same operations on consecutive data-frames and the sync pulse tells all the logical operators when the begining and end of each frame is. 
![image](https://github.com/user-attachments/assets/90f56cd2-8004-4443-863a-dab21486d713)

## FFT
The FFT block implements a highly optimized Radix-2 decomposition Decimation In Frequency Fast Fourier Transform on parallel inputs. It takes a user-defined shift schedule as input (`pfb_fft_shift`) and records overflow events in a the register named `fft_of_count`. This FFT implementation takes advantage of the fact that a real-to-complex DFT has half as many outputs as inputs to balance the fact that it's being fed two samples from each ADC simultaneously. It also incorporates a de-scrambler so that the outputs are frequency-ordered complex samples (DIF FFTs naturally scramble their output (frequency domain samples) into bit-reversed order).
![image](https://github.com/user-attachments/assets/014abde5-64bb-4092-b4dc-71730cd42abf)

*TODO: inside the FFT*

## TVG1

The first Test Vector Generator follows immediately downstream of the FFT. TVGs are gateware testing/debugging units that, when deployed in the field, are configured to litterally not do anything to the signal. (The two green `bus_create`/`bus_expand` blocks don't modify the data whatsoever but simply package the 36/72 parallel bit-lines together/appart.)

![image](https://github.com/user-attachments/assets/e13b4aa7-9dc6-4208-8208-d4010bb2a379)

A TVG enables the developer to mux in values from a user-writeable BRAM instead of the input. This module helps to test and debug gateware at both the simulation stage and in-Silica. The user controls whether to let actual data pass by writing to the `enable` register, and what data to replace it with by writing to the `data` BRAM. 

![image](https://github.com/user-attachments/assets/b5756967-1c7b-4401-be73-cd9cb4c15e45)

## Requantization

After the PFB (and TVG), each FFT'd signal branches three ways:

- The on-board correlator (skip ahead to the [correlator section](gateware-design.md#on-board-correlator))
- 4-bit requantization
- 1-bit requantization

The latter two paths requantize the same complex digital signal to 1+1-bit and 4+4-bits (in parallel). Each of the real and imaginary components of each sample is quantized to one and four bits. 

Data re-ordering and bussifying follows both one-bit and four-bit requantization stages. The output order is defined by the user so that the frequency channels to be packetized come out first. Both 1bit and 4bit data is 'bussified' onto an 8-bit bus. 8-bits is not wide enough for the 4-bit data (4 bits ADC0 real + 4 bits ADC0 imaginary + 4 bits ADC1 real + 4 bits ADC1 imaginary = 16 bits per clock), which is why the re-order stage must come before the bussifying stage. This limits the number of selectable channels to 1024 of 2048. 

![image](https://github.com/user-attachments/assets/848b1a53-7618-4bd3-bf80-89c43f1fb128)

For example, if you were interested in channels 420 and above, you would configure the re-order and transpose stages to output signals illustrated in the timing diagram below. These are the signals you would see if you were to put a scope (or a logic analyzer) right before the MUX that selects whether to transmit 1-bit or 4-bit requantized signals to the next stage. The data lines below represent a byte-wide bus carrying quantized, complex data from both ADC channels, so there are 16 bits per frequency channel in 4-bit mode, and 4 bits per frequency channel in 1-bit mode. 

<script type="WaveDrom">
{
  "signal": [
    {"name": "clk", "wave": "p......"},
    {},
    {"name": "sync (4-bit)", "wave": "010...."},
    {"name": "four-bit data", "wave": "x.4.4.4", "data": ["Channel 420", "Channel 421", "Ch 422"], "phase": 0},
    {},
    {"name": "sync (1-bit)", "wave": "0.10..."},
    {"name": "one-bit data", "wave": "x..4444", "data": ["420/1", "422/3", "424/5", "426/7"], "phase": 0}
  ],
  "config": {
    "hscale": 2,
    "skin": "narrow"
  },
  "head": {
    "text": "Four-bit vs One-bit Data Streams with Sync Pulses"
  },
  "foot": {
    "text": "Data streams with single-pulse sync signals"
  }
}
</script>

The one bit re-quantization logic is just a bunch of comparators (> or <). 

![image](https://github.com/user-attachments/assets/17cac276-9a76-438d-895c-24e5632b1e61)

In parallel we quantize each component (real/imaginary) of each frequency channel to four bits. To exploit the full range of bits excersised by 4-bit quantization we apply digital gain to each frequency channel individually. The gain in each channel is set by the user through the `coeffs_pol0`/`coeffs_pol1` registers. The result is saturated against a floor and ceiling of the 4-bit range (-/+0.875) to wrapping (overflow). This image shows the logic for one of four quantization signal paths is shown.

![image](https://github.com/user-attachments/assets/681d4e86-7b5c-44b6-9e64-b2f9b52ff31f)

## Payload Packetiser

The payload packetiser is a logical subsystem that creates payloads for the UDP packets which are broadcast over ethernet on SFP0. It bundles re-quantized data, either 1-bit or 4-bit quantized, with the spectrum number, which counts the number of FFTs which have been performed so that we can tell 1) whether we have dropped any UDP packets and 2) which UDP packets we have dropped. The logic that generates UDP packet headers and bundles these with our payloads is taken care of by a Xilinx IP. Our payload packetiser subsystem is directly upstream of this UDP packetiser logic and interfaces with it over three busses: data (8 bits wide), valid line (1 bit), end-of-frame line (EOF, 1 bit). Pull the valid line high simultaneously with valid data (data that you want to transmit) on your eight-lane bus, and low when the data on the data bus is trash. A UDP payload buffer fills up with valid data until you pull the end-of-frame line high simultaneously with the last valid data point. 

![image](https://github.com/user-attachments/assets/d4f9f32a-99fe-4119-9472-fe3d81c45a14)

*Caption: the payload packetizer subsystem is the white block labelled 'packetiser'. It has three input busses and three output busses, but it also takes input from readable and writable registers hidden beneath the subsystem mask.*

For example, lets say we have one bit data and the only channels we care about are 420 through 427 inclusive, the timing diagram at the input of the payload packetiser, as we saw above in the requantization section, looks something like the following. 

<script type="WaveDrom">
{
  "signal": [
    {"name": "clk", "wave": "p......"},
    {"name": "data", "wave": "xx4444x", "data": ["420/1", "422/3", "424/5", "426/7"]},
    {"name": "sync", "wave": "010...."},
  ],
  "config": {
    "hscale": 2,
    "skin": "narrow"
  },
  "head": {
    "text": "Payload Packetiser Upstream"
  },
  "foot": {
    "text": "Timing diagram upstream of payload packetiser."
  }
}
</script>

The sync pulse is only generated once and the logic is synchronised only once, so every subsequent input will have only the data line with anything of interest on it. The downstream logic knows to expect the pattern to repeat every 2048 clocks. The timing diagram downstream of the payload packetiser looks alternatively like either of the following three diagrams. 

<script type="WaveDrom">
{
  "signal": [
      {"name": "clk", "wave": "p......"},
    ["First",
      {"name": "data", "wave": "x333344", "data": ["Spec#","Spec#","Spec#","Spec#", "420/1", "422/3"]},
      {"name": "valid", "wave": "01....."},
      {"name": "EOF", "wave": "0......"},
    ],
    ["Middle",
      {"name": "data", "wave": "x4444xx", "data": ["420/1", "422/3","424/5", "426/7"]},
      {"name": "valid", "wave": "01...0."},
      {"name": "EOF", "wave": "0......"},
    ],
    ["Final",
      {"name": "data", "wave": "x4444xx", "data": ["420/1", "422/3","424/5", "426/7"]},
      {"name": "valid", "wave": "01...0."},
      {"name": "EOF", "wave": "0...10."},
    ]

  ],
  "config": {
    "hscale": 2,
    "skin": "narrow"
  },
  "head": {
    "text": "Payload Packetiser Downstream"
  },
}
</script>

User facing registers tell the packetiser 1) how many FFT frames go into each packet and 2) how many clocks the valid pulse should last on each frame--which is directly related to the number of channels we want to preserve. Lets take a closer look at the logic that accomplishes the generation and pulsing.  


![image](https://github.com/user-attachments/assets/7c499f13-fe07-4ca6-aa7e-0b83687c7edd)

The sync and reset lines trigger a reset of the FFT-frame (/spectrum) counter, "spectra-counter". This counter is a UFix 43 bit counter, the most significant 32-bits are sliced and bussified onto a byte-wide bus. These four bytes populate the first four bytes of each UDP packet payload. This spectrum number is written to disk as per specified in our data format [need link to data format spec]. The 11th LSB is also sliced out and used to trigger a "new spectra" pulse. This pulse which anounces a new FFT-frame or "spectrum" is multi-purposes, it: 

- synchronises the 32-bit spectrum number bussifier (so that the bits come out in sync with the first valid data point)  

![image](https://github.com/user-attachments/assets/84a8d566-3856-4534-b621-6db6178840a4)

- increments another counter, "packet_spec_counter", by one which, in turn,  
    - triggers the valid line on the first spectrum of the packet to include the spectrum number
    - triggers the end-of-frame line on the last spectrum of the packet to tell the UDP packetizer to bundle and send the buffered payload. The user sets the spectra per packet from python by writing an integer to the (above) yellow "spectra_per_packet" register. 

![image](https://github.com/user-attachments/assets/e536e121-464c-4b61-8093-ad520ceb6ea3)

- triggers a pulse-extender that pulls high the valid line for the number of clocks required to for each spectrum. The user sets the number of bytes in each spectrum by writing said value into the (above) yellow "bytes_per_spectrum" register. The number of bytes in each spectrum is a function of the number of channels saved as well as the re-quantization depth (4+4 bits vs 1+1 bit per sample). 

![image](https://github.com/user-attachments/assets/8282f16c-8bed-42e3-9695-06b7bc48a5c7)

Once the data is packetized, it's checked into the `one_gbe` block, and the CASPER framework takes care of the plumbing to pipe this into the correct Xilinx IP that implements UDP packetizing, and routs it to the correct physical SFP port (SFP0). In the image, a helpful user-readable buffer-overflow counter `tx_of_cnt` keeps track of overflowing packets, and the signal coming out of our user-defined packetizer also routs *in simulation only* to a virtual oscilascope.

![image](https://github.com/user-attachments/assets/81af2f1e-c9aa-4a68-b5d5-fb50447d2e5a)

## On-board correlator

The signal path branches after the FFT. In the previous section we looked at re-quantization, data selection, and UDP packetizing, here we look at the second branch down-stream of the FFT: the correlator. The correlator computes auto- and cross-correlations of both channelized signals. The power in each pol is computed with a simple accumulator. Real and imaginary components of the cross correlation are similarly calculated. The result is dumped periodically into addressable BRAM registers `pol00`, `pol11`, `pol01r`, `pol01i`. Mathematically, the correlator computes autocorrelations, 

$$P_{00}[k] = \sum_{l=0}^{N-1}|y_0[k,l]|^2,$$

and cross correlations,

$$P_{01}[k] = \sum_{l=0}^{N-1}y_0[k,l] \cdot y_1[k,l]^\ast,$$

where $y_s[k,l]$ is the $l$'th spectrum's $k$'th frequency channel's data from pol-$s$. Real and imaginary terms of the cross-correlations are accumulated in seperate BRAMs as all the arithmetic is carried out on real integers. 

![image](https://github.com/user-attachments/assets/b76d2983-9580-4acd-8d1c-ef4f29060695)

### Correlator accumulator book-keeping

It's important to do some book-keeping to make sure the correlator BRAMs don't overflow. If the signal is `U37_36` and the accumulator BRAM is `U64_35` then we can only accumulate `2^28` samples samples (per channel), in seconds the accumulator BRAM fills up in `2^28*4096/250e6 = 4398` seconds, which is over an hour. We will never want to accumulate more than a few seconds. 

However, the calculus changes if we implement FFT bit-growth to avoid doing a full shift schedule. If we grow the data by one bit on every FFT butterfly stage we're eating up 12 bits, which means that it becomes logically possible for the accumulator BRAMs to overflow after only one second, which is unacceptable. This means we either have to grow our BRAMs or do something to reduce the bit depth of these numbers. 

The latest version of the firmware implements 8-bits of bitgrowth, the full twelve is not needed as our 12 bit data is already LSB-padded by four bits in the stack-and-sum stage of the PFB (upstream of the FFT). After eight bits of growth in the FFT the data is 24 bits wide; four LSBs are sliced off in the correlator branch so that it fits snugly in the correlator's accumulators. 

## User read/writeable registers

We make use of all named addressable registers in this design so it's worth knowing what each of them does. (The left-pointing pentagonal tags mean *goto* and are paired with right-pointing ones of the same name.)

- `gbe_en` GigaBit Ethernet interface ENable. Single bit, 0 for disable, 1 for enable.
- `gbe_rst` GigaBit Ethernet interface ReSeT. Single bit. Resets on transition from 0 to 1. 
- `pack_rst` PACKetizer ReSeT. Single bit to reset packetizer logic, including spectrum counter, on transition from 0 to 1.
- `cnt_rst` accumulator CoNTroller ReSeT. Single bit to reset accumulator control logic.
- `acc_len` ACCumulation LENgth. UFix32 sets the number of spectra to accumulate for each correlation. (How long to integrate data, if you prefer to think that way.) This number times 4096/250e6 gives the accumulation time in seconds.
- `dest_ip` Sets the DESTination IP addresss.
- `dest_prt` Sets the DESTination PoRT.
- `sync_cnt` (read only) does exactly nothing because I removed the logic that periodically syncs all the logic. Instead it just syncs stuff once on initialization. 
- `acc_cnt` (read_only) ACCumulation CouNTer. Counts the number of spectra that have been accumulated.

![image](https://github.com/user-attachments/assets/dc35ab2c-af51-4d35-8757-cc842d6fa51f)

Other user read/writeable registers are scattered throughout the design. 

`sync_adc` SYNChronize ADC logic. Single bit pulse active on transition from 0 to 1.

![image](https://github.com/user-attachments/assets/e336dff3-952b-436f-8287-6e3adeff3513)

`sync` Creates SYNChronizing pulse that aligns each set of the DSP chain. Single bit pulse, active on transition from 0 to 1.

![image](https://github.com/user-attachments/assets/32370d0a-f7d8-4995-b09a-27cb45661cee)

`pfb_fft_shift` UFix12 determines the shift schedule. Each bit represents 0 for no shift, 1 for shift. Currently we have a full shift schedule. We may want to implement a bit-growth FFT so that we can have our cake (low noise floor from not shifting) and eat it too (no FFT overflows).

![image](https://github.com/user-attachments/assets/cb700aac-7c46-4e74-89d4-23321878be34)

`fft_of_count` (read only) FFT OverFlow COUNTer. Every time there's an overflow event in a frame +1 is added to this UFix32 register. 

![image](https://github.com/user-attachments/assets/4000552f-d857-4f4f-9528-039c2766a375)

`sel` SELects which requantization bit mode to choose from: 0 for 1bit, 1 for 4bits. 

![image](https://github.com/user-attachments/assets/db427b50-23b6-4954-b8ca-67176bf47ce7)

`tvg1_enable` Enables the the TVG right after the FFT stage. 0 to pass actual data, 1 to pass values read sequentially from the BRAM labelled `data`.  

![image](https://github.com/user-attachments/assets/965644f1-5e7f-4e35-bacd-4cbea44bc282)

`tvg16bit_enable` enables the the TVG right after the 4bit requantization stage. Write 0 to pass actual data, 1 to pass values read sequentially from the BRAM labelled `data`. 



![image](https://github.com/user-attachments/assets/92f41e80-d411-49e6-a489-9bc1cd704244)

`four_bit_quant_clip_count` *TODO*

![image](https://github.com/user-attachments/assets/61d9f33b-769a-4a5d-a905-d28dbd13ec01)


`spectra_per_packet` *TODO*

![image](https://github.com/user-attachments/assets/ce1b0a74-604e-4658-a7f9-52226a5e6038)

`bytes_per_spectrum` *TODO*

![image](https://github.com/user-attachments/assets/8a3a2dc9-285b-496d-9a9a-5f2839976327)

`tx_of_cnt` *TODO*

![image](https://github.com/user-attachments/assets/63ea5bae-0e51-4440-b4ee-a6fb8e3c42be)


## User BRAM interfaces

`tvg1_data` *TODO*

![image](https://github.com/user-attachments/assets/f1de49f6-9061-4ba1-b7b4-c27abf0b19de)

`tvg16bit_data` *TODO*

Examples of this TVG's use can be found [here](https://github.com/ALBATROS-Experiment/sparrow-albatros/blob/main/software/tvg_4bitq.py). 

<details>
<summary>View example use</summary>

```python
--8<-- "software/tvg_4bitq.py"
```
</details>


![image](https://github.com/user-attachments/assets/04c53ba1-43c8-422d-bc29-7924458afd7a)

`four_bit_quant_coeffs_pol0/1` *TODO*

![image](https://github.com/user-attachments/assets/7125f44c-2cc7-484d-9558-ac815d39058f)

![image](https://github.com/user-attachments/assets/816aa56a-8e1f-4ce0-bb5f-e6100a04847f)

`one_bit_reorder_map1` *TODO*

![image](https://github.com/user-attachments/assets/5f86f08d-6f42-462d-9d6c-76480f68d785)

`four_bit_reorder_map1` *TODO*

![image](https://github.com/user-attachments/assets/a05cf769-554a-4171-aab9-7abd4db8154f)

`pol00`, `pol11`, `pol01r`, `pol01i` *TODO*

![image](https://github.com/user-attachments/assets/0badcd5c-f85f-4ed7-b32b-421b398a638c)







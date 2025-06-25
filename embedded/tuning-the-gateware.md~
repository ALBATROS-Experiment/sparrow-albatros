# Tuning the Gateware from Python

This section is about how to configure the gateware once the FPGA has been programmed. This means writing to a sequence of registers and BRAMs to:

- Synchronize the logic
- Select requantization depth (4-bit / 1-bit)
- Set FFT parameters
- Set the cross correlation parameters
- Select frequency channels
- Autotune the digital gain coefficients (4-bit mode only) 

The [Design Overview](../gateware/gateware-design.md) section documents how the gateware is designed in Simulink. If you are unfamiliar with gateware design or are finding this section confusing you may want to read that section before this one.

## Reading and Writing to Programmable Registers

In Python the CasperFpga class allows you to interface with named FPGA registers. The gateware needs to be tuned and configured according to the user's needs, such as which channels to pick and which what bit mode to select. This configuration happens in five steps. 

- Setup. TODO
- Set the channel order. Re-order the frequency channels so that the UDP payload packetizer selects the correct channels. For example, to select only channels 120:136 you must re-order the channels so that 120:136 occur at the beginning of each frame. For deeper explanation of why we need to do this see the [packetizer section](../gateware/gateware-design.md#packetiser). 
- Optionally set the 4 bit coefficients. 
- Tune. TODO
- Optionally update the 4 bit coefficients based on OBC data. TODO


## Setup 

TODO: write this section... 

::: sparrow_albatros.AlbatrosDigitizer.setup

## Set channel order

TODO: write this section... 

::: sparrow_albatros.AlbatrosDigitizer.set_channel_order

## Tuning registers

TODO: write this section... 

::: sparrow_albatros.AlbatrosDigitizer.tune


## Tuning the 4-bit digital gain coefficients (special case)

TODO: write this section... here's an outline: 

- To avoid non-converging, iterative hell of capturing 4 bit data and increasing or decreasing the digital gain coefficients on each channel (that may take forever to converge in the intermittent RFI case), we one-shot the 4-bit gain coefficients by getting a power reading from the on-board-correlator. 
- Tune gateware so that it's collecting data as you'd like it to
- Wait for the on board correlator's accumulator to fill up
- Read the auto-correlations power in each channel to estimate the optimal digital-gain coefficient needed
- Write the set the 4-bit digital gain coefficients. 

Now to actually implement this requires some book-keeping. 

## Bookkeeping with bit-growth

See also [release notes of bit growth FFT implementation](https://github.com/ALBATROS-Experiment/sparrow-albatros/blob/5feccd8c8ff970ebfc55a5a0953bfbcbe9106edf/firmware/sparrow_albatros_spec/outputs/sparrow_albatros_spec_2025-04-17-xc7z030-35_release-notes.md).

Fix24_23s come out of the FFT, real and complex are bussed together and interpreted as UFix_48s. The power block outputs UFix_42_40, which is a shifted squared value. We drop the six LSBs to make room for MSBs in the 64-bit accumulator. 

![image](https://github.com/user-attachments/assets/c39c0825-3314-4014-9529-d37757e5df3b)

The number of spectra accumulated in the auto-correlator is denoted `len_acc` or $L$. The best estimate for the STD in each real and imaginary components is 

$$
\sigma = \sqrt{\frac{P}{2 \cdot 2^40 \cdot L}}
$$

where $P$ is the power read from the autocorr BRAM interpreted as a UInt64. The four-bit digital gains must be set so that the quantization interval $\Delta$ is equal to 0.293 of the STD (see the [Optimal Digital Gains section](#digital-gain-coefficients-4bit)). In this implementation, the quantization interval remains fixed at 1/8 and the digital gains modify the signals. 

![image](https://github.com/user-attachments/assets/bb581028-d1bf-489a-970d-cb04fa4ee619)

We must therefore multiply the signals by a gain factor, $g$, such that 

$$
g \cdot \sigma = \frac{1/8}{0.293} \Rightarrow g = \frac{1/8}{0.293 \cdot \sigma}.
$$

This factor is written to BRAM as a `UInt_32` but it's reinterpreted as a `Fix_32_17`, so we need to multiply $g$ by $2^{17}$ before writing it. The following is a code snippet for computing the optimal gain.

```python
pol00 = read_pols(['pol00','pol11'])['pol00'] / (1<<40) # Each freq channel has different power
stds0 = np.sqrt(pol00 / (2 * acc_len))                  # ...and therefore a different STD
gs = (1/8) / (0.293 * stds0)                            # Calculate the digital gains
gs *= (1<<17)                                           # Multiply by 2^17 for packaging
gs[np.where(gs > (1<<31)-1)] = (1<<31)-1                # Clip the gains so that they fit
# Now the `gs` array is ready for writing to BRAM
```

...as implemented in 

::: sparrow_albatros.AlbatrosDigitizer.get_optimal_coeffs_from_acc 

## The communication stack

You may be wondering how Python is able to read from and write to FPGA registers. 

<TODO: explain how the gateware is configured with user read/write-able registers. Start with a section explaining the communication stack, how the python code talks to the tcpborphserver over http, how this server is configured as a service controlled by systemctl, the tcp borph server talks to (which chip?) over SPI, how the SPI commands talk to the FPGA, how the CASPER framework implements a piece of SPI logic that recieves commands and writes/reads data to/from programable registers. Finish this off with a paragraph about how the CASPER framework implements .fpg files after binary implementation, also reference the compile, synthesis, implementation.>






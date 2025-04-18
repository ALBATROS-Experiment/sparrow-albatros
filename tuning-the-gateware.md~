# Tuning the Gateware from Python

The [Design Overview](gateware-design.md) section documents how the gateware is designed diagramatically in Matlab at a high level of abstraction. If you are unfamiliar with gateware design or are finding this section confusing you may want to read that section before this one.

### Reading and Writing to Programmable Registers

In Python the CasperFpga class allows you to interface with named FPGA registers. The gateware needs to be tuned and configured according to the user's needs, such as which channels to pick and which what bit mode to select. This configuration happens in five steps. 

- Setup. TODO
- Set the channel order. Re-order the frequency channels so that the UDP payload packetizer selects the correct channels. For example, to select only channels 120:136 you must re-order the channels so that 120:136 occur at the beginning of each frame. For deeper explanation of why we need to do this see the [packetizer section](gateware-design.md#packetiser). 
- Optionally set the 4 bit coefficients. 
- Tune. TODO
- Optionally update the 4 bit coefficients based on OBC data. TODO


### Setup 

::: sparrow_albatros.AlbatrosDigitizer.setup


### Set channel order

::: sparrow_albatros.AlbatrosDigitizer.set_channel_order

### Tune

::: sparrow_albatros.AlbatrosDigitizer.tune

### The communication stack

You may be wondering how Python is able to read from and write to FPGA registers. 

<TODO: explain how the gateware is configured with user read/write-able registers. Start with a section explaining the communication stack, how the python code talks to the tcpborphserver over http, how this server is configured as a service controlled by systemctl, the tcp borph server talks to (which chip?) over SPI, how the SPI commands talk to the FPGA, how the CASPER framework implements a piece of SPI logic that recieves commands and writes/reads data to/from programable registers. Finish this off with a paragraph about how the CASPER framework implements .fpg files after binary implementation, also reference the compile, synthesis, implementation.>






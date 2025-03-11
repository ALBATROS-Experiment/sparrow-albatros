"""Example of writing to TVG"""

import numpy as np

fpga.read("tvg16bit_data", 16, offset=0)

# 32 bit registers but 16bit LSB are sliced (i.e. 16 MSB are sliced off)
tvgbytes=np.ndarray.tobytes(np.array([0x0,0x0,0x05,0xaf]*(1<<11),dtype='>i1'))

fpga.write("tvg16bit_data", tvgbytes, offset=0)

fpga.write("")

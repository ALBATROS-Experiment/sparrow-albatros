"""Example of writing to TVG"""

#import numpy as np
#
#fpga.read("tvg16bit_data", 16, offset=0)
#
## 32 bit registers but 16bit LSB are sliced (i.e. 16 MSB are sliced off)
#tvgbytes=np.ndarray.tobytes(np.array([0x0,0x0,0x05,0xaf]*(1<<11),dtype='>i1'))
#
#fpga.write("tvg16bit_data", tvgbytes, offset=0)

#def pack_into_4bit_tvg(pol0r:bytes, pol0i:bytes, pol1r:bytes, pol1i:bytes):
#    """Pack complex arrays into TVG right after 4bit requantizer"""
#    for p in (pol0r,pol0i,pol1r,pol1i):assert len(p)==(1<<10)
#    zeros=b'\x00'*(1<<10)

###################

TVG_FFT_SBRAM_SHAPE = (1<<11,)

def pack_into_64(pol0r, pol0i, pol1r, pol1i):
    """Pack complex arrays into the TVG right after FFT block.

    Numpy doesn't know about fix_16_15's, so we'll just use int16
    and pretend that they are the fractional part, i.e. that our int16s
    represent that number divided by (1<<15)=32_768.

    :param np.ndarray(int16) pol0r:
        Real componant of FFT'd pol0
    :param np.ndarray(int16) pol0i:
        Imaginary componant of FFT'd pol0
    :param np.ndarray(int16) pol1r:
        Real componant of FFT'd pol1
    :param np.ndarray(int16) pol1i:
        Imaginary componant of FFT'd pol1

    :returns: Bytearray, ready for writing to sbram.
    """
    # TODO: figure out endianness...
    for pol in (pol0r, pol0i, pol1r, pol1i):
        assert pol.shape==TVG_FFT_SBRAM_SHAPE, "Pol shape must be compatible with sbram shape"
    out = np.array([pol0r, pol0i, pol1r, pol1i], dtype='>i2').T.flatten()
    return out.tobytes()


def pack_tvg_fft_ramp_pol0r(fpga):
    """Write to the TVG data register"""
    pol0r = np.arange(1<<11, dtype='>i2')
    pol0i = np.zeros(1<<11, dtype='>i2')
    pol1r = np.zeros(1<<11, dtype='>i2')
    pol1i = np.zeros(1<<11, dtype='>i2')
    fpga.write("tvg1_data", pack_into_64(pol0r, pol0i, pol1r, pol1i), offset=0)
    return

def pack_tvg_fft_ramp_pol0i(fpga):
    pol0r = np.zeros(1<<11, dtype='>i2')
    pol0i = np.arange(1<<11, dtype='>i2')
    pol1r = np.zeros(1<<11, dtype='>i2')
    pol1i = np.zeros(1<<11, dtype='>i2')
    fpga.write("tvg1_data", pack_into_64(pol0r, pol0i, pol1r, pol1i), offset=0)
    return

def pack_tvg_fft_ramp_pol1r(fpga):
    pol0r = np.zeros(1<<11, dtype='>i2')
    pol0i = np.zeros(1<<11, dtype='>i2')
    pol1r = np.arange(1<<11, dtype='>i2')
    pol1i = np.zeros(1<<11, dtype='>i2')
    fpga.write("tvg1_data", pack_into_64(pol0r, pol0i, pol1r, pol1i), offset=0)
    return

def pack_tvg_fft_ramp_pol1i(fpga):
    pol0r = np.zeros(1<<11, dtype='>i2')
    pol0i = np.zeros(1<<11, dtype='>i2')
    pol1r = np.zeros(1<<11, dtype='>i2')
    pol1i = np.arange(1<<11, dtype='>i2')
    fpga.write("tvg1_data", pack_into_64(pol0r, pol0i, pol1r, pol1i), offset=0)
    return

def pack_tvg_fft_const_pol0r(fpga):
    pol0r = np.ones(1<<11, dtype='>i2')
    pol0i = np.zeros(1<<11, dtype='>i2')
    pol1r = np.zeros(1<<11, dtype='>i2')
    pol1i = np.zeros(1<<11, dtype='>i2')
    fpga.write("tvg1_data", pack_into_64(pol0r, pol0i, pol1r, pol1i), offset=0)
    return

def pack_tvg_fft_const_pattern2(fpga):
    pol0r = np.ones(1<<11, dtype='>i2')
    pol0i = np.zeros(1<<11, dtype='>i2')
    pol1r = np.ones(1<<11, dtype='>i2') * 2
    pol1i = np.zeros(1<<11, dtype='>i2')
    fpga.write("tvg1_data", pack_into_64(pol0r, pol0i, pol1r, pol1i), offset=0)
    return

def pack_tvg_fft_const_pattern3(fpga):
    pol0r = np.zeros(1<<11, dtype='>i2')
    pol0r[np.array((400,401,403,406,410,415,421,428))] = 1
    pol0i = np.zeros(1<<11, dtype='>i2')
    pol1r = np.zeros(1<<11, dtype='>i2')
    pol1i = np.zeros(1<<11, dtype='>i2')
    fpga.write("tvg1_data", pack_into_64(pol0r, pol0i, pol1r, pol1i), offset=0)
    return

def pack_tvg_fft_pol0r(fpga,pol0r):
    pol0i = np.zeros(1<<11, dtype='>i2')
    pol1r = np.zeros(1<<11, dtype='>i2')
    pol1i = np.zeros(1<<11, dtype='>i2')
    fpga.write("tvg1_data", pack_into_64(pol0r, pol0i, pol1r, pol1i), offset=0)
    return

def pack_tvg_fft_pol0r_pol1r(fpga,pol0r,pol1r):
    pol0i = np.zeros(1<<11, dtype='>i2')
    pol1i = np.zeros(1<<11, dtype='>i2')
    fpga.write("tvg1_data", pack_into_64(pol0r, pol0i, pol1r, pol1i), offset=0)
    return

def zeros_tag(chan_idx):
    arr=np.zeros(1<<11, dtype='>i2')
    arr[chan_idx] = 1<<14
    arr=np.array(arr,dtype='>i2')
    return arr

def negrailed_tag(chan_idx):
    arr=np.array(np.ones(1<<11) * (-1<<14),dtype='>i2')
    arr[chan_idx] = 1<<14
    arr=np.array(arr,dtype='>i2')
    return arr

if __name__=="__main__":
    # tests
    pass

#pols=[np.concatenate([[1]*44,[-1],[1]*((1<<11)-45)]),np.concatenate([[1]*45,[-1],[1]*((1<<11)-46)]),np.ones(1<<11),np.ones(1<<11)];fpga.write("tvg1_data",pack_into_64(pols[0],pols[1],pols[2],pols[3]),offset=0)


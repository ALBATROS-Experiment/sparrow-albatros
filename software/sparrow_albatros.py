import os
import struct
import time
import numpy as np
import ads5404
import adf4351

# Design register names
SS_NAME = "ss_adc"

def str2ip(ip):
    iplist = list(map(int, ip.split('.')))
    ipint = 0
    for i in range(4):
        ipint += (iplist[i] << (8*(3-i)))
    return ipint

def ip2str(ipint):
    ip=""
    for i in range(4):
        shift = (3-i)*8
        ip += str((ipint & (0b11111111<<shift)) >> shift)
        ip += '.'
    return ip[:-1]

class SparrowAlbatros():
    def __init__(self, cfpga, fpgfile=None, adc_clk=250):
        """
        Constuctor for SparrowAdc2Tge control instance.

        :param cfpga: CasperFpga instance for Sparrow board connection
        :type cfpga: casperfpga.Casperfpga

        :param fpgfile: .fpg file to associate with running firmware. If
            none is provided, certain methods will be unavailable until
            either `program_fpga` or `read_fpgfile` are called.
        :type fpgfile: str

                :param adc_clk: ADC sample rate in MHz
                :type adc_clk: float
        """
        self.cfpga = cfpga
        self.adc_clk = adc_clk
        self.adc = ads5404.Ads5404(cfpga)
        self.pll = adf4351.Adf4351(cfpga, out_freq=adc_clk)
        self.fpgfile = None
        if fpgfile is not None:
            self.read_fpgfile(fpgfile)

    def initialize_adc(self):
        """
        Initialize ADC interface.
        """
        self.adc.chip_reset()
        self.adc.hw_reset()
        self.adc.enable_readback()
        self.adc.init()
        self.sync_adc()

    def sync_adc(self):
        """
        Send a sync pulse to the ADC
        """
        self.cfpga.write_int("sync_adc", 0)
        self.cfpga.write_int("sync_adc", 1)
        self.cfpga.write_int("sync_adc", 0)

    def get_adc_temp(self):
        """
        Get ADC temperature.

        :return: temerature in degrees C
        :rtype: int
        """
        return self.adc.get_temp()

    def read_fpgfile(self, fpgfile):
        """
        Associate running firmware with give .fpg file.
        This does _not_ program the FPGA. For that, use `program_fpga()`.
        This is a shortcut to casperfpga's get_system_information.

        :param fpgfile: .fpg file to read
        :type fpgfile: str
        """
        if not os.path.isfile(fpgfile):
                raise RuntimeError("%s is not a file" % fpgfile)
        self.fpgfile = fpgfile
        try:
            self.cfpga.get_system_information(fpgfile)
        except:
            print("Could not process fpgfile %s. Maybe the FPGA is not programmed yet?" % fpgfile)

    def program_fpga(self, fpgfile=None):
        """
        Program the FPGA with the provided fpgfile,
        or self.fpgfile if none is provided.

        :param fpgfile: .fpg file to program. If None, the fpgfile
            provided at instantiation time will be programmed.
        :type fpgfile: str
        """
        self.fpgfile = fpgfile or self.fpgfile
        if self.fpgfile is None:
            raise RuntimeError("Don't know what .fpg file to program!")
        self.cfpga.upload_to_ram_and_program(self.fpgfile)
        time.sleep(0.3)
        self.pll.configure()
        time.sleep(0.3)
        self.adc.power_enable()

    def get_adc_snapshot(self, use_pps_trigger=False):
        """
        Get a snapshot of ADC samples simultaneously captured from
        both ADC channels.

        :param use_pps_trigger: If True, use the DSP pipeline's PPS trigger to
            start capture. Otherwise, capture immediately.
        :type use_pps_trigger: bool

        :return: x, y; a pair of numpy arrays containing a snapshot of ADC
            samples from ADC channel 0 and 1, respectively.
        :rtype: (numpy.ndarray, numpy.ndarray)
        """
        if not SS_NAME in self.cfpga.snapshots.keys():
            raise RuntimeError("%s not found in design. Have you provided an appropriate .fpg file?" % SS_NAME)
        ss = self.cfpga.snapshots[SS_NAME]
        d, t = ss.read_raw(man_trig=not use_pps_trigger)    
        v = np.array(struct.unpack(">%dh" % (d["length"]//2), d["data"]))
        x = v[0::2]
        y = v[1::2]
        return x, y

class AlbatrosDigitizer(SparrowAlbatros):
    def __init__(self, cfpga, fpgfile=None, adc_clk=250., logger=None):
        """
        Constructor binds logger, as well as parent attributes (cfpga, etc.). 
        """
        super().__init__(cfpga, fpgfile, adc_clk)
        self.logger = logger # TODO: sort out logging, default logger?
        return 

    def print_regs(self):
        """Prints contents of registers."""
        print(f"dest_ip\t\t{ip2str(self.cfpga.registers.dest_ip.read_uint())}")
        print(f"gbe_en\t\t{self.cfpga.registers.gbe_en.read_uint()}")
        print(f"gbe_rst\t\t{self.cfpga.registers.gbe_rst.read_uint()}")
        print(f"bytes-per-spec\t{self.cfpga.registers.packetiser_bytes_per_spectrum.read_uint()}")
        print(f"spec-per-pack\t{self.cfpga.registers.packetiser_spectra_per_packet.read_uint()}")
        print(f"sync\t\t{self.cfpga.registers.sync.read_uint()}")
        print(f"tx_of_cnt\t{self.cfpga.registers.tx_of_cnt.read_uint()}")
        print(f"sync_cnt\t{self.cfpga.registers.sync_cnt.read_uint()}")

    def set_channel_order(self, channels, bits):
        """Sets the firmware channels"""
        if bits==1:
            raise NotImplementedError(f"1 bit mode has not yet been implemented")
        elif bits==4:
            channel_map="four_bit_reorder_map1" # hard coded name of fpga bram name
        else:
            raise ValueError(f"Bits must be 1 or 4, not {bits}")
        self.cfpga.write(channel_map, channels.astype(">H").tostring(), offset=0) # .tostring ret bytes

    def set_channel_coeffs(self, coeffs_pol0, coeffs_pol1, bits):
        """coeffs must be array of type '>I'"""
        if bits==1:
            self.logger.info("In one bit mode. No need to write coeffs.")
            return 
        elif bits==4:
            self.logger.info("Setting four bit coeffs.")
            self.cfpga.write("four_bit_quant_coeffs_pol0", coeffs_pol0.tobytes(), offset=0)
            self.cfpga.write("four_bit_quant_coeffs_pol1", coeffs_pol1.tobytes(), offset=0)
        return 

    def sync_pulse(self):
        """The firmware is designed so that pack_rst and cnt_rst set some 
        internal state to zero that the sync pulse sets to one. Without
        doing pack_rst and cnt_rst before pulseing the sync, things are 
        not properly synced up and bad things happen."""
        self.logger.info("Resetting packetizer")
        self.cfpga.registers.pack_rst.write_int(0)
        self.cfpga.registers.pack_rst.write_int(1)
        self.cfpga.registers.pack_rst.write_int(0)
        self.logger.info("Resetting acc control and syncing")
        self.cfpga.registers.cnt_rst.write_int(0) # Acc control reset pulse 
        self.cfpga.registers.cnt_rst.write_int(1)
        self.cfpga.registers.cnt_rst.write_int(0)
        self.logger.info("Sending pulse")
        time.sleep(0.3)
        self.cfpga.registers.sync.write_int(0) # Sync pulse must come after acc cntrl reset
        self.cfpga.registers.sync.write_int(1) 
        self.cfpga.registers.sync.write_int(0) 

    def setup(self):
        self.logger.info("Programming FPGA")
        self.program_fpga()
        fpga_clock_mhz = self.cfpga.estimate_fpga_clock()
        self.logger.info(f"Estimated FPGA clock is {fpga_clock_mhz:.2f}")
        self.logger.info("Initializing ADCs")
        self.initialize_adc()

    def tune(self, ref_clock, fftshift, acc_len, dest_ip, 
            dest_prt, spectra_per_packet, bytes_per_spectrum, dest_mac:int=0):
        """
        Setup the FPGA firmware by tuning the input registers.
        Perform sanity check on each after setting the value. 
        - Assumes fpga has been programmed and cfpga is running. 
        - Sets values in FPGA's programmable Registers and BRAMs. 
        - Basic health checks of FPGA output values, e.g. overflows. 

        :param ref_clock: Reference clock in MHz. 
        :type ref_clock: float (int?)

        :param fftshift: Register Value. FFT shift schedule, bits 1/0 for on/off.
        :type fftshift: int
        :param acc_len: RV. Number of spectra accumulated to integrate correlations. 
        :type acc_len: int
        :param dest_ip: RV. IP address to send packets to. Turn into int before writing. 
        :type dest_ip: str
        :param dest_prt: RV. Packet destination port number. 
        :type dest_prt: int
        :param spectra_per_packet: RV. Number of specs to write in each UDP packet. 
        :type spectra_per_packet: int
        :param bytes_per_spectrum: RV. Number of bytes in one, quantized spec. 
        :type bytes_per_spectrum: int

        JF reccomends using netcat for writing packets to file for test. 
        """
        MTU=1500 # max number of bytes in a packet
        assert spectra_per_packet < (1<<5), "spec-per-pack too large for slice, aborting"
        assert spectra_per_packet * bytes_per_spectrum <= MTU-8, "Packets too large, will cause fragmentation"
        # Assume bitstream already uploaded, data in self.cfpga
        # Assume ADCs already initialized including that get_system_information...
        # Inherit adc's logger level
        self.adc.ref = ref_clock # Set reference clock for ADC
        # ADC calibration assumed already aligned (?)
        # Need to set the ADC gain?
        # Get info from and set registers 
        self.logger.info(f"FPGA clock: {self.cfpga.estimate_fpga_clock():.2f}")
        self.logger.info(f"Set FFT shift schedule to {fftshift:b}")
        self.cfpga.registers.pfb_fft_shift.write_int(fftshift)
        self.logger.info(f"Set correlator accumulation length to {acc_len}")
        self.cfpga.registers.acc_len.write_int(acc_len)
        # This firmware only has 4-bit qutnziation
        self.logger.info("Reset GBE (UDP packetizer)")
        self.cfpga.registers.gbe_rst.write_int(1)
        self.cfpga.registers.gbe_en.write_int(0)
        self.logger.info(f"Set spectra-per-packet to {spectra_per_packet}")
        self.cfpga.registers.packetiser_spectra_per_packet.write_int(spectra_per_packet)
        self.logger.info(f"Set bytes-per-spectrum to {bytes_per_spectrum}")
        self.cfpga.registers.packetiser_bytes_per_spectrum.write_int(bytes_per_spectrum)
        self.logger.info(f"NOT YET IMPLEMENTED: Setting destination MAC address to {dest_mac}")
        # TODO: set destination MAC address
        self.logger.info(f"Set destination IP address and port to {dest_ip}:{dest_prt}")
        self.cfpga.registers.dest_ip.write_int(str2ip(dest_ip))
        self.cfpga.registers.dest_prt.write_int(dest_prt)
        # Do we need to set mac address?
        self.sync_pulse()
        fft_of_count = self.cfpga.registers.fft_of_count.read_uint()
        if fft_of_count != 0:
            self.logger.warning(f"FFT overflowing: count={fft_of_count}")
        else:
            self.logger.info(f"No FFT overflows detected")
        self.logger.info("Enabling 1 GbE output")
        self.cfpga.registers.gbe_en.write_int(1)
        #self.logger.info("Leaving GBE reset high; pull it down manually once you think the negotiation has happened well!")
        self.cfpga.registers.gbe_rst.write_int(0)
        gbe_overflow = self.cfpga.registers.tx_of_cnt.read_uint()
        if gbe_overflow:
            self.logger.warning(f"GbE transmit overflowing: count={gbe_overflow}")
        else:
            self.logger.info("No GbE overflows detected")
        self.logger.info("Setup and tuning complete")
        return

    def setup_and_tune(self,**kwargs):
        self.setup()
        self.tune(**kwargs)

    def read_pols(self, pols, struct_format=">2048q"):
        pols_dict = {}
        for pol in pols:
            pols_dict[pol] = np.array(struct.unpack(struct_format, self.cfpga.read(pol, 2048*8)), dtype="int64")
        return pols_dict

    def get_optimal_coeffs_from_acc(self, chans):
        """Reads accumulator to set 4-bit digital gain coefficients

        Assumes fpga is setup and well tuned.

        self : AlbatrosDigitizer object for reading the acc
        chans : numpy integer array can be used to index accumulator pols"""
        _pols = self.read_pols(['pol00','pol11'])
        # these are read as int64 but they are infact 64_35 for autocorr and 64_34 for xcorr
        pol00,pol11 = _pols['pol00'] / (1<<36), _pols['pol11'] / (1<<36) 
        acc_len = self.cfpga.registers.acc_len.read_uint() # number of spectra to accumulate
        pol00_stds = np.sqrt(pol00 / (2*acc_len)) # stds of re or imaginary parts
        pol11_stds = np.sqrt(pol11 / (2*acc_len)) 
        # for the same channel, we want to apply same digital gain to each pol
        quant4_delta = 1/8  # 0.125 is the quantization delta for 4-bit signed 4_3 as on fpga
                            # clips at plus/minus 0.875
        quant4_optimal = 0.353 # optimal 15-level quantization delta for gaussian with std=1
        coeffs_pol0 = np.zeros(2048) # hard coded num of chans as 2048
        coeffs_pol1 = np.zeros(2048) # hard coded num of chans as 2048
        coeffs_pol0[chans] = quant4_delta / (pol00_stds[chans] * quant4_optimal)
        coeffs_pol1[chans] = quant4_delta / (pol11_stds[chans] * quant4_optimal)
        coeffs_pol0[chans] *= (1<<18)/2 # bram is re-interpreted as ufix 32_17
        coeffs_pol1[chans] *= (1<<18)/2 # bram is re-interpreted as ufix 32_17
        # not sure where missing factor of two comes from 
        # sets stds to roughly 2.83 [plus-minus systematic 0.05])
        coeffs_pol0[coeffs_pol0 > (1<<31)-1] = (1<<31)-1 # clip coeffs at max signed-int value
        coeffs_pol1[coeffs_pol1 > (1<<31)-1] = (1<<31)-1 # clip coeffs at max signed-int value
        coeffs_pol0 = np.array(coeffs_pol0 + 0.5, dtype='>I')
        coeffs_pol1 = np.array(coeffs_pol1 + 0.5, dtype='>I')
        return coeffs_pol0,coeffs_pol1

    def set_channels(self, channels:list):
        """
        Set reorder BRAMs to reorder channels before selection.

        :param channels: A list or array of the channels to select. 
        """
        # TODO: implement this
        return 

    def get_adc_stats(self):
        """
        
        ss_adc_ctrl register
        bit0: Put a posedge here to enable a new capture.
        bit1: Ignore external trigger and trigger immediately.
        bit2: Ignore external write enable and capture on every FPGA clock.
        bit3: Continuously capture data until we get an external stop command.
        bits4-to-31: 28 bits for number of valid data samples to skip after trigger before starting capture. 

        To capture a snapshot, I assume 'a capture' fills the whole BRAM with 
        ADC samples. I think we want to pulse bit0, hold bit1 high, bit2 high, 
        bit3 low. These first four bits are the LSBs, the LSB is bit0, because
        it is sliced out and pos-edged. Therefore bitN must be the N'th LSB.
        """
        #mask_skip =0xfffffff0
        #mask_capt =0b1000
        #mask_trig =0b0110
        #mask_pulse=0b0001
        #skip =0b1<<26 # wait 0.5 seconds ~1<<(15+12-1), mostly out of superstition
        #trig =0b11
        #capt =0b0  # hold this low to not continuously capture data (?) uncertain
        #ctrl_pulse_on =((skip<<4) & mask_skip) | ((capt<<3) & mask_capt) | ((trig<<1) & mask_trig) | (0b1 & mask_pulse)  
        #ctrl_pulse_off=((skip<<4) & mask_skip) | ((capt<<3) & mask_capt) | ((trig<<1) & mask_trig) | (0b0 & mask_pulse)  
        #adc_stats={}
        ## TODO
        self.logger.warning("get_adc_stats not yet implemented")
        return None

    def read_registers(self, regs):
        """regs is a list of register names, reads uint and returns dict of vals"""
        reg_dict = {}
        for r in regs:
            reg_dict[r] = np.array(self.cfpga.registers[r].read_uint())
        return reg_dict








import argparse
import time
import numpy as np
import sys
import os
from os.path import join
from configparser import ConfigParser
import utils
import logging
import datetime
import lbtools_l

import casperfpga
from sparrow_albatros import *

# Set system time from LB timestamp
with open("set_gps_clock.py") as f:exec(f.read()) 

parser=argparse.ArgumentParser(description="Script to save baseband to disk")
parser.add_argument('-l','--loggerlevel', type=str, default='INFO', help='Level of the logger, default is INFO, (Options are: DEBUG, INFO, WARNING)')
parser.add_argument('-c','--configfile', type=str, default='/home/casper/sparrow-albatros/software/config.ini', help='.ini file with parameters to configure firmware')
args=parser.parse_args()

# Set up the logger
logger=logging.getLogger('albatros_dump_baseband')
if args.loggerlevel.upper() == 'INFO':
    logger_level = logging.INFO
elif args.loggerlevel.upper() == 'DEBUG':
    logger_level = logging.DEBUG
elif args.loggerlevel.upper() == 'WARNING':
    logger_level = logging.WARNING
else:
    raise Exception(f"Did not recognise logger level {args.loggerlevel.upper()}")
logger.setLevel(logger_level)
logger.propagate=False # log messages are passed to handlers of logger's ancestors

# Load config file
config_file=ConfigParser()
config_file.read(args.configfile)

# Logger settings
logger=logging.getLogger("sparrow_albatros_dump_baseband")
logger.propagate=False
logger.setLevel(logging.INFO)
LOG_DIRECTORY=config_file.get("paths", "log_directory")
configfpga_log_dir=join(LOG_DIRECTORY, "configfpga")
if not os.path.isdir(configfpga_log_dir):
    os.makedirs(configfpga_log_dir)
file_logger=logging.FileHandler(join(configfpga_log_dir,f"albatros_configfpga_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"))
file_logger.setFormatter(logging.Formatter("%(asctime)s %(name)s %(message)s", "%Y-%m-%d %H:%M:%S"))
file_logger.setLevel(logging.INFO)
logger.addHandler(file_logger)
# Logger to stdout
stdout_logger=logging.StreamHandler(sys.stdout)
stdout_logger.setLevel(logging.INFO)
logger.addHandler(stdout_logger)

## Get relevant parameters from config file & write log
logger.info("Parsing config.ini for relevant values")
MAX_BYTES_PER_PACKET=config_file.getint("networking", "max_bytes_per_packet")
CHANNELS_STRING=config_file.get("baseband", "channels")
COEFFS_STRING=config_file.get("baseband", "coeffs")
BITS=config_file.getint("baseband", "bits") # 1 or 4
FPGFILE=config_file.get("paths", "fpgfile")
DEST_IP=config_file.get("fpga_register_vals", "dest_ip")
DEST_PRT=config_file.getint("fpga_register_vals", "dest_prt")
ADC_CLK=config_file.getint("baseband", "adc_clk") # 250, but can differ depending on firmware
ACC_LEN=config_file.getint("fpga_register_vals", "accumulation_length")
chans=utils.get_channels_from_str(CHANNELS_STRING, BITS)
logger.info("chans", chans)
coeffs=utils.get_coeffs_from_str(COEFFS_STRING)
spectra_per_packet=utils.get_nspec(chans, max_nbyte=MAX_BYTES_PER_PACKET)
bytes_per_spectrum=chans.shape[0]
logger.info(f"Spec per packet: {spectra_per_packet}")
logger.info(f"Bytes per spectrum: {bytes_per_spectrum}")


logger.info("Writing bitstream to FPGA and initializing...")
host="10.10.11.99" # TODO: read from config.ini
fpga=casperfpga.CasperFpga(host,transport=casperfpga.KatcpTransport)
sparrow=AlbatrosDigitizer(fpga,FPGFILE,ADC_CLK,logger)
sparrow.setup()
sparrow.set_channel_order(chans, BITS)
sparrow.set_channel_coeffs(coeffs, coeffs, BITS)
sparrow.tune(ref_clock=ADC_CLK,
        fftshift=0xffff, # TODO: integrate this, get this from config.ini
        acc_len=ACC_LEN,
        dest_ip=DEST_IP,
        dest_prt=DEST_PRT,
        spectra_per_packet=spectra_per_packet,
        bytes_per_spectrum=bytes_per_spectrum,
        bits=BITS)

#sparrow.cfpga.registers.gbe_en.write_int(0) # don't vomit packets everywhere



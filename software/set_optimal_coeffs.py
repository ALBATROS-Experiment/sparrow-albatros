import argparse
from configparser import ConfigParser
import sys
import datetime
import logging
import casperfpga
import utils
from sparrow_albatros import *
from os.path import join

parser=argparse.ArgumentParser(description="Script to set optimal coefficients")
parser.add_argument('-l','--loggerlevel',type=str,default='INFO', help='Level of the logger, defaults to INFO, (Options are: DEBUG, INFO, WARNING)')
parser.add_argument('-c','--configfile',type=str,default='/home/casper/sparrow-albatros/software/config.ini', help='.ini fiel with parameters to configure firmware')
args=parser.parse_args()


# Set up the logger
logger=logging.getLogger('albatros_set_optimal_coeffs')
if args.loggerlevel.upper()=='INFO':
    logger_level = logging.INFO
elif args.loggerlevel.upper()=='DEBUG':
    logger_level = logging.DEBUG
elif args.loggerlevel.upper()=='WARNING':
    logger_level = logging.WARNING
else:
    raise Exception(f"Did not recognise logger level {args.loggerlevel.upper()}")
logger.setLevel(logger_level)
logger.propagate=False # log messages passed to handlers of logger's ancestors

# Load config file
config_file=ConfigParser()
config_file.read(args.configfile)

# Logger settings
LOG_DIRECTORY = config_file.get("paths", "log_directory")
logdir=join(LOG_DIRECTORY, "set_optimal_coeffs")
if not os.path.isdir(logdir):
    os.makedirs(logdir)
file_logger=logging.FileHandler(join(logdir,f"albatros_set_optimal_coeffs_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")) 
file_logger.setFormatter(logging.Formatter("%(asctime)s %(name)s %(message)s", "%Y-%m-%d %H:%    M:%S")) 
file_logger.setLevel(logging.INFO)
logger.addHandler(file_logger)
# Logger to stdout
stdout_logger=logging.StreamHandler(sys.stdout)
stdout_logger.setLevel(logging.INFO)
logger.addHandler(stdout_logger)


# Get relevane parameters from config file
FPGFILE=config_file.get("paths", "fpgfile")
BITS=config_file.getint("baseband", "bits")
CHANNELS_STRING=config_file.get("baseband", "channels")
COEFFS_POL0_BINARY_PATH=config_file.get("paths", "coeffs_pol0_binary_path")
COEFFS_POL1_BINARY_PATH=config_file.get("paths", "coeffs_pol1_binary_path")
ADC_CLK=config_file.getint("baseband", "adc_clk")
HOST=config_file.get("networking", "host")
assert BITS!=1, "No point in autotuning if we're quantizing to one bit"

logger.info("Init-ing casperfpga object")
fpga=casperfpga.CasperFpga(HOST,transport=casperfpga.KatcpTransport)
logger.info("Init-ing AlbatrosDigitizer object")
sparrow=AlbatrosDigitizer(fpga,FPGFILE,ADC_CLK,logger)
# Assumes FPGA already setup and running
logger.info("Assuming FPGA already up and running, no need to reprogram")
logger.info("Parsing channels from config.ini channels string")
chans_fpga=utils.get_channels_from_str(CHANNELS_STRING, BITS)
coeffs_pol0, coeffs_pol1 = sparrow.get_optimal_coeffs_from_acc(chans_fpga[::2]) # dtype '>I' big endian long
logger.info("Setting coeffs on the FPGA")
sparrow.set_channel_coeffs(coeffs_pol0, coeffs_pol1, bits=BITS)
logger.info("Writing coeffs to secret binary for handoff to dump_baseband.c")
with open(COEFFS_POL0_BINARY_PATH,"wb") as f:
    f.write(np.array(coeffs_pol0[chans_fpga[::2]],dtype='<Q').tobytes())
with open(COEFFS_POL1_BINARY_PATH,"wb") as f:
    f.write(np.array(coeffs_pol1[chans_fpga[::2]],dtype='<Q').tobytes())





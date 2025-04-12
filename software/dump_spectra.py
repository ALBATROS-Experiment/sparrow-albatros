import casperfpga
import argparse
import datetime
from configparser import ConfigParser
import logging
import os
from os.path import join, isdir
import scio # pip install pbio
import struct
import sparrow_albatros
import time
import numpy as np
import lbtools_l
import sys

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("-c", "--configfile", type=str, default="config.ini", help="Config file that defines DAQ software parameters including data storage paths, fpga register values, and other configuration variables.")
    parser.add_argument("-d", "--debug", action="store_true", help="Print log info to stdout")
    args=parser.parse_args()
    config_file=ConfigParser()
    config_file.read(args.configfile)
    use_gps=True # use GPS reference clock to set timestamps

    # Set up logger 
    logger=logging.getLogger("dump_spectra")
    logger.propagate=False
    logger.setLevel(logging.INFO)
    LOG_DIR=join(config_file.get("paths", "log_directory"), "spectra")
    if not isdir(LOG_DIR):
        os.makedirs(LOG_DIR)
    file_logger=logging.FileHandler(join(LOG_DIR, f"albatros_spectra_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"))
    file_format=logging.Formatter("%(asctime)s %(name)s %(message)s", "%Y-%m-%d %H:%M:%S")
    file_logger.setFormatter(file_format)
    file_logger.setLevel(logging.INFO)
    logger.addHandler(file_logger)
    if args.debug:
        stdout_logger=logging.StreamHandler(sys.stdout)
        stdout_logger.setLevel(logging.INFO)
        logger.addHandler(stdout_logger)

    # Read configuration 
    logger.info("#"*50)
    HOST=config_file.get("networking", "host")
    logger.info(f"# (1) Sparrow board IP address: {HOST}")
    ACC_LEN=config_file.getint("fpga_register_vals", "accumulation_length")
    logger.info(f"# (2) Correlator accumulation length: {ACC_LEN}")
    SPECTRA_OUTPUT_DIR=config_file.get("paths", "dump_spectra_output_directory")
    logger.info(f"# (3) Spectra output directory: {SPECTRA_OUTPUT_DIR}")
    POLS=config_file.get("fpga_register_vals", "pols")
    logger.info(f"# (4) Pols: {POLS}")
    METADATA_REGISTERS=config_file.get("fpga_register_vals", "metadata_registers")
    logger.info(f"# (5) Metadata registers: {METADATA_REGISTERS}")
    COMPRESS_SCIO_FILES=config_file.get("spectra", "compress_scio_files")
    if COMPRESS_SCIO_FILES=="None": COMPRESS_SCIO_FILES=None
    logger.info(f"# (6) Compress scio files: {COMPRESS_SCIO_FILES}")
    DIFF_SCIO_FILES=config_file.getboolean("spectra", "diff_scio_files")
    logger.info(f"# (7) Diff scio files: {DIFF_SCIO_FILES}")
    logger.info(f"# (8) Log directory is: {LOG_DIR}")
    FPGFILE=config_file.get("paths", "fpgfile")
    logger.info(f"# (9) Bitstream (.fpg) file path: {FPGFILE}")
    ADC_CLK=config_file.get("baseband", "adc_clk")
    logger.info(f"# (10) ADC clock set to: {ADC_CLK}")
    logger.info("#"*50)

    try:
        fpga=casperfpga.CasperFpga(HOST,transport=casperfpga.KatcpTransport)
        sparrow=sparrow_albatros.AlbatrosDigitizer(fpga,FPGFILE,ADC_CLK,logger)
        #sparrow.cfpga.get_system_information(FPGFILE) # need this?
        pols=POLS.split()
        metadata_registers=METADATA_REGISTERS.split()
        if use_gps:
            gps_tstamp = lbtools_l.lb_read()[0]
            if gps_tstamp is None:
                logger.info("Trying to use GPS clock but unable to read from LB.")
            else:
                logger.info("LB GPS clock successfully read.")
        else:
            logger.info("Not using LB GPS clock. Timestamps will come from system clock.")
        while True:
            adc_stats=sparrow.get_adc_stats() # Not yet implemented
            start_time = time.time()
            if start_time < 1e5:
                logger.warning("Start time in acquire data seems to be near zero")
            time_frag = str(start_time)[:5]
            outsubdir = join(SPECTRA_OUTPUT_DIR, time_frag, str(np.int64(start_time)))
            os.makedirs(outsubdir)
            logger.info(f"Writing current data to {outsubdir} ADC bits used: ({'Not implemented'}) ({'Not implemented'})")
            start_raw_files = {}
            end_raw_files = {}
            scio_files = {}
            if use_gps:
                file_gps_timestamp1 = open(join(outsubdir,"time_gps_start.raw"),"w")
                file_gps_timestamp2 = open(join(outsubdir,"time_gps_stop.raw"),"w")
            file_sys_timestamp1 = open(join(outsubdir,"time_sys_start.raw"),"w")
            file_sys_timestamp2 = open(join(outsubdir,"time_sys_stop.raw"),"w")
            file_adc_temp = open(join(outsubdir,"adc_temp.raw"),"w")
            for register in metadata_registers:
                start_raw_files[register] = open(join(outsubdir,f"{register}1.raw"),"w")
                end_raw_files[register] = open(join(outsubdir,f"{register}2.raw"),"w")
            for pol in pols:
                scio_files[pol] = scio.scio(join(outsubdir,f"{pol}.scio"), 
                        diff=DIFF_SCIO_FILES, 
                        compress=COMPRESS_SCIO_FILES)
            for adc in ["adc0","adc1"]:
                scio_files[adc] = scio.scio(join(outsubdir,f"{adc}.scio"),
                        diff=DIFF_SCIO_FILES,
                        compress=COMPRESS_SCIO_FILES)
            acc_cnt = 0
            while time.time()-start_time < 60*60: # new folder every hour
                # read accumulation count from FPGA registers
                new_acc_cnt = sparrow.cfpga.registers.acc_cnt.read_uint() 
                if new_acc_cnt > acc_cnt:
                    if use_gps:
                        startread = lbtools_l.lb_read()
                        start_gps_timestamp = startread[0] 
                    start_sys_timestamp = time.time()
                    start_reg_data = sparrow.read_registers(metadata_registers)
                    pol_data = sparrow.read_pols(pols, ">2048q")
                    end_reg_data = sparrow.read_registers(metadata_registers)
                    end_sys_timestamp = time.time()
                    if use_gps:
                        endread = lbtools_l.lb_read()
                        end_gps_timestamp = endread[0]
                    read_time = end_sys_timestamp - start_sys_timestamp
                    if use_gps:
                        if start_gps_timestamp is None:
                            start_gps_timestamp = 0
                        if end_gps_timestamp is None:
                            end_gps_timestamp = 0
                    if start_reg_data["acc_cnt"] != end_reg_data["acc_cnt"]:
                        logger.warning("Accumulation counter changed during read")
                    adcss0_data,adcss1_data = sparrow.get_adc_snapshot()
                    for register in metadata_registers:
                        np.array(start_reg_data[register]).tofile(start_raw_files[register])
                        start_raw_files[register].flush()
                        np.array(end_reg_data[register]).tofile(end_raw_files[register])
                        end_raw_files[register].flush()
                    np.array(start_sys_timestamp).tofile(file_sys_timestamp1)
                    np.array(sparrow.get_adc_temp()).tofile(file_adc_temp)
                    np.array(end_sys_timestamp).tofile(file_sys_timestamp2)
                    if use_gps:
                        np.array(start_gps_timestamp, dtype=np.uint32).tofile(file_gps_timestamp1)
                        np.array(end_gps_timestamp, dtype=np.uint32).tofile(file_gps_timestamp2)
                    file_sys_timestamp1.flush() 
                    file_adc_temp.flush() 
                    file_sys_timestamp2.flush()
                    if use_gps:
                        file_gps_timestamp1.flush()
                        file_gps_timestamp2.flush()
                    for pol in pols:
                        scio_files[pol].append(pol_data[pol])
                    scio_files["adc0"].append(adcss0_data)
                    scio_files["adc1"].append(adcss1_data)
                time.sleep(0.9) # wait so that while loop not always going
            for pol in pols:
                scio_files[pol].close()
            scio_files["adc0"].close()
            scio_files["adc1"].close()
            for register in metadata_registers:
                start_raw_files[register].close()
                end_raw_files[register].close()
            file_sys_timestamp1.close()
            file_adc_temp.close()
            file_sys_timestamp2.close()
            if use_gps:
                file_gps_timestamp1.close()
                file_gps_timestamp2.close()
    finally:
        logger.info(f"Terminating DAQ at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")



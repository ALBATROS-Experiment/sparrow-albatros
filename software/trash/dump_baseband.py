import casperfpga
from sparrow_albatros import AlbatrosDigitizer, str2ip
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
import struct
import pcapy
import dpkt

IP_HEADER_START = 14 # Safe to assume for Ethernet, but not for other link layers
UDP_HEADER_START = IP_HEADER_START + 20 # 20 bytes is the smallest IPV4 header size w/o options
UDP_PAYLOAD_START = UDP_HEADER_START + 8 # udp header is 8 bytes

def unpack_4bit(buf):
    """Takes raw bytes, returns complex numpy array"""
    raw=np.frombuffer(buf,'int8')
    re=np.asarray(np.right_shift(np.bitwise_and(raw, 0xf0), 4), dtype='int8')
    re[re>8]=re[re>8]-16
    im=np.asarray(np.bitwise_and(raw, 0x0f), dtype='int8')
    im[im>8]=im[im>8]-16
    vec=1J*im+re # complex vector
    return vec

def unpack_packet(packet_raw_eth_frame, bits, spec_per_packet, bytes_per_packet):
    packet = packet_raw_eth_frame[UDP_PAYLOAD_START:UDP_PAYLOAD_START + bytes_per_packet]
    assert len(packet)==bytes_per_packet, "packet too small" # prob need try-catch
    specno = np.frombuffer(packet, '>I', 1)
    if bits==4:
        vec=unpack_4bit(packet[4:])
        nchan=(len(vec)//spec_per_packet)//2
        pol0=np.reshape(vec[::2], [spec_per_packet, nchan])
        pol1=np.reshape(vec[1::2], [spec_per_packet, nchan])
    return pol0, pol1

def get_4bit_packet_channel_stats(cap, acc_len, spec_per_packet, bytes_per_packet):
    """Takes 

    cap : udp packet reader (pcapy.open_live object)
    acc_len : int, the number of specs to accumulate
    spec_per_packet : 
    """
    # Read a bunch of packets
    npack=(acc_len + spec_per_packet - 1)//spec_per_packet
    pol0,pol1,specno=[None]*npack,[None]*npack,[None]*npack
    for i in range(npack):
        rawpack = cap.next()[1]
        specno[i] = np.frombuffer(rawpack[UDP_PAYLOAD_START:UDP_PAYLOAD_START + bytes_per_packet], '>I', 1)[0]
        pol0[i],pol1[i] = unpack_packet(rawpack, 4, spec_per_packet, bytes_per_packet)
    # Estimate stdev in each channel
    pol0,pol1 = np.vstack(pol0)[:acc_len,:], np.vstack(pol1)[:acc_len,:]
    std0re = np.std(np.real(pol0),axis=0)
    std0im = np.std(np.imag(pol0),axis=0)
    std1re = np.std(np.real(pol1),axis=0)
    std1im = np.std(np.imag(pol1),axis=0)
    return std0re,std0im,std1re,std1im,pol0,pol1,specno

def write_header(file_object, chans, spec_per_packet, bytes_per_packet, bits):
    have_trimble = True
    header_bytes = 8*10 + 8*len(chans) # 8 bytes per element in the header
    gpsread = lbtools_l.lb_read()
    gps_time = gpsread[0]
    if gps_time is None:
        logger.info('File timestamp coming from Sparrow clock. This is unreliable.')
        have_trimble = False
        gps_time = time.time()
    #print('GPS time is now ', gps_time)
    file_header=np.asarray([header_bytes, bytes_per_packet, len(chans), spec_per_packet, bits, have_trimble], dtype='>Q')
    file_header.tofile(file_object)
    np.asarray(chans, dtype=">Q").tofile(file_object)
    gps_time=np.asarray([0, gps_time], dtype='>Q') # setting gps_week = 0 to flag the new header format with GPS ctime timestamp
    gps_time.tofile(file_object)
    lat_lon = gpsread[1]
    if lat_lon is None:
        logger.info("Can't speak to LB, so no position information")
        latlon={}
        latlon['lat']=0
        latlon['lon']=0
        latlon['elev']=0
    else:
        latlon={}
        latlon['lat']=lat_lon[3]
        latlon['lon']=lat_lon[2]
        latlon['elev']=lat_lon[4]
        #print('lat/lon/elev are ',latlon['lat'],latlon['lon'],latlon['elev'])

    latlon=np.asarray([latlon['lat'],latlon['lon'],latlon['elev']],dtype='>d')
    latlon.tofile(file_object)

if __name__=="__main__":
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
    baseband_log_dir=join(LOG_DIRECTORY, "baseband")
    if not os.path.isdir(baseband_log_dir):
        os.makedirs(baseband_log_dir)
    file_logger=logging.FileHandler(join(baseband_log_dir,f"albatros_dump_baseband_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"))
    file_logger.setFormatter(logging.Formatter("%(asctime)s %(name)s %(message)s", "%Y-%m-%d %H:%M:%S"))
    file_logger.setLevel(logging.INFO)
    logger.addHandler(file_logger)
    # Logger to stdout
    stdout_logger=logging.StreamHandler(sys.stdout)
    stdout_logger.setLevel(logging.INFO)
    logger.addHandler(stdout_logger)

    ## Get relevant parameters from config file & write log
    #logger.info("#"*50)
    DEST_IP=config_file.get("fpga_register_vals", "dest_ip")
    #logger.info(f"# (1) Arm processor IP address: {SNAP_IP}")
    DEST_PRT=config_file.getint("fpga_register_vals", "dest_prt")
    #logger.info(f"# (2) UDP packet destination port: {dest_prt}")
    FILE_SIZE=config_file.getfloat("baseband", "file_size")
    HOST=config_file.get("networking", "host")
    MAX_BYTES_PER_PACKET=config_file.getint("networking", "max_bytes_per_packet")
    CHANNELS_STRING=config_file.get("baseband", "channels")
    BITS=config_file.getint("baseband", "bits") # 1 or 4
    FPGFILE=config_file.get("paths", "fpgfile")
    COEFFS_BINARY_PATH=config_file.get("paths", "coeffs_binary_path")
    ADC_CLK=config_file.getint("baseband", "adc_clk")

    ## Construct FPGA and AlbatrosDigitizer (SparrowAlbatros) object without tuning
    fpga=casperfpga.CasperFpga(HOST,transport=casperfpga.KatcpTransport)
    sparrow=AlbatrosDigitizer(fpga,FPGFILE,ADC_CLK,logger)

    ## ==== Set up comms ====
    max_bytes=65565
    #sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #bufsize=sock.getsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF)
    #logger.info(f"UDP buf size in bytes: {bufsize}")
    ## timeout prevents hanging on sock.recvfrom_into(packet, bytes_per_packet) after overheat
    #sock.settimeout(10)
    #try:
    #    sock.bind((DEST_IP, DEST_PRT))
    #    #sock.bind(('0.0.0.0', DEST_PRT))
    #    logger.info(f"Connected to {DEST_IP}:{DEST_PRT}")
    #except:
    #    logger.error(f"Cannot bind to {DEST_IP}:{DEST_PRT}")

    #sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(3))
    #sock.bind(('eth0', 0))
    snaplen, promisc, timeout_ms = 65535, 1, 1000
    cap = pcapy.open_live('eth0', snaplen, promisc, timeout_ms)
    #cap.set_buffer_size(200 * 1024 * 1024)
    cap.setfilter("udp and dst port 7417 and dst host 10.10.11.99 and src host 192.168.41.10")
    UDP_PORT = 7417

    chans_fpga=utils.get_channels_from_str(CHANNELS_STRING, BITS)
    # chans_fpga is a sequence made for the fpga reorder block, channels is an array for numpy 
    spec_per_packet=utils.get_nspec(chans_fpga, max_nbyte=MAX_BYTES_PER_PACKET)
    print('chans shape',chans_fpga.shape)
    print('chans_fpga',chans_fpga)
    bytes_per_spectrum=chans_fpga.shape[0] # number of bytes per spectrum in both channels
    print(f"Spec per packet: {spec_per_packet}")
    print(f"Bytes per spectrum: {bytes_per_spectrum}")
    bytes_per_packet=bytes_per_spectrum*spec_per_packet+4 #the 4 extra bytes is for the spectrum number
    #packet=bytearray(bytes_per_packet)
    num_of_packets_per_file=int(FILE_SIZE*1.0e9/bytes_per_packet)
    spec_per_file = spec_per_packet * num_of_packets_per_file
    logger.info(f"Spectra per packet: {spec_per_packet}")
    logger.info(f"Bytes per packet: {bytes_per_packet}")
    logger.info(f"Num packets per file: {num_of_packets_per_file}")
    logger.info(f"Num spectra per file: {spec_per_file}")
    
    # Autotuning
    if BITS==4:
        logger.warning(f"Polling accumulators to get coeffs, need to wait at least two accs before doing this reliably.")
        coeffs = sparrow.get_optimal_coeffs_from_acc(chans_fpga[::2]) # dtype '>I', big endian long
        sparrow.set_channel_coeffs(coeffs, 4)
        # little endian uint64 '<Q', easier to read for C program
        coeffs_to_serialize = np.array(coeffs[chans_fpga[::2]],dtype='<Q')
        with open(COEFFS_BINARY_PATH,"wb") as f:
            f.write(coeffs_to_serialize.tobytes())
            logger.info(f"Coeffs written to temp file: {COEFFS_BINARY_PATH}")
    # Figure out drive situation
    # TODO
    # copy from here: https://github.com/ALBATROS-Experiment/albatros_daq/blob/py38_port/new_daq/dump_baseband.py#L27

    # Write baseband
    # for now just this hacky thing, assume the drive has been mounted and has space
    bbpath="/media/BASEBAND/baseband"
    assert os.path.isdir(bbpath), "Drive not mounted, crashing program"
    print("bytes_per_packet", bytes_per_packet)
    #input("[Enter to continue, ^c to exit]")
    while True:
        dirtime=str(int(time.time()))[:5] # first five digitis of ctime
        if not os.path.isdir(join(bbpath, dirtime)):
            os.mkdir(join(bbpath, dirtime))
        fname=f"{int(time.time())}.raw"
        fpath=join(bbpath, dirtime, fname)
        with open(fpath, "wb", buffering=20*1024*1024) as bbfile:
            write_header(bbfile, chans_fpga, spec_per_packet, bytes_per_packet, BITS)
            for i in range(num_of_packets_per_file):
                #print(i,end=',')
                try:
                    (header, packet) = cap.next()
                    bbfile.write(packet[UDP_PAYLOAD_START:UDP_PAYLOAD_START + bytes_per_packet])
                    sn = int.from_bytes(packet[UDP_PAYLOAD_START:UDP_PAYLOAD_START + 4], byteorder='big', signed=False)
                    if i == 0:
                        start_sn = sn
                except Exception as e:
                    logger.warning(f"Ignoring exception {e}")
                    continue
        print(f"num packets per file {num_of_packets_per_file}")
        print(f"spec_per_packet {spec_per_packet}")
        print(f"sn {sn}")
        print(f"start sn {start_sn}")
        missing_frac = 1. - float(num_of_packets_per_file * spec_per_packet)/(sn - start_sn + spec_per_packet)
        perc_missing = missing_frac * 100
        logger.info(f"Wrote file to {fpath}. Missing percentage of packets is {perc_missing:.5f}")















#!/usr/bin/env python3
import os
import time
import datetime
import numpy as np
import logging
import signal
import sys
from pathlib import Path
import argparse

# Import required libraries and modules
import casperfpga
from sparrow_albatros import SparrowAlbatros

def setup_logging(log_dir):
    """Set up logging with timestamp-based filename"""
    # Create log directory if it doesn't exist
    log_dir = Path(log_dir)
    log_dir.mkdir(exist_ok=True, parents=True)
    
    # Create timestamp for log filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"monitor_adc-{timestamp}.log"
    log_path = log_dir / log_filename
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger()

def analyze_adc_snapshot(x, y):
    """
    Analyze ADC snapshot data and return useful metrics
    
    Args:
        x (numpy.ndarray): Snapshot from ADC channel 0
        y (numpy.ndarray): Snapshot from ADC channel 1
        
    Returns:
        dict: Dictionary of metrics
    """
    metrics = {}
    
    # Power calculation (mean of squares)
    metrics['power_ch0'] = np.mean(x**2)
    metrics['power_ch1'] = np.mean(y**2)
    
    # Min/Max values
    metrics['min_ch0'] = np.min(x)
    metrics['max_ch0'] = np.max(x)
    metrics['min_ch1'] = np.min(y)
    metrics['max_ch1'] = np.max(y)
    
    # Standard deviation
    metrics['std_ch0'] = np.std(x)
    metrics['std_ch1'] = np.std(y)
    
    # Count of saturated samples
    # Assuming the ADC is 12-bit signed, max range would be -2048 to 2047
    # These are the saturation thresholds for a 12-bit ADC
    adc_max = 2047
    adc_min = -2048
    
    metrics['saturated_samples_ch0'] = np.sum((x >= adc_max) | (x <= adc_min))
    metrics['saturated_samples_ch1'] = np.sum((y >= adc_max) | (y <= adc_min))
    
    # Calculate percentage of saturated samples
    metrics['saturated_percent_ch0'] = 100.0 * metrics['saturated_samples_ch0'] / len(x)
    metrics['saturated_percent_ch1'] = 100.0 * metrics['saturated_samples_ch1'] / len(y)
    
    return metrics

def main():
    """Main function to monitor ADC snapshots"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Monitor ADC snapshots and log metrics")
    parser.add_argument("--interval", type=int, default=10, 
                        help="Interval between snapshots in seconds (default: 10)")
    parser.add_argument("--log-dir", type=str, 
                        default=os.path.expanduser("~/monitor_adc"),
                        help="Directory to store log files (default: ~/monitor_adc)")
    parser.add_argument("--fpga-host", type=str, default="10.10.11.99",
                        help="FPGA hostname or IP address (default: 10.10.11.99)")
    parser.add_argument("--fpg-file", type=str, default=None,
                        help="Optional .fpg file to associate with running firmware")
    args = parser.parse_args()
    
    # Set up logging
    logger = setup_logging(args.log_dir)
    logger.info(f"Starting ADC monitoring with interval of {args.interval} seconds")
    
    # Set up signal handler for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Received signal to terminate, shutting down...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Connect to FPGA without changing its state
    try:
        # Create FPGA connection
        cfpga = casperfpga.CasperFpga(args.fpga_host, transport=casperfpga.KatcpTransport)
        
        # Initialize SparrowAlbatros instance without programming FPGA
        # We want to read the ADC state without changing anything
        sparrow = SparrowAlbatros(cfpga, fpgfile=args.fpg_file, adc_clk=250)
        
        # If fpg_file is provided, read it to get system information
        # This doesn't program the FPGA, just provides context for interacting with it
        if args.fpg_file and os.path.exists(args.fpg_file):
            sparrow.read_fpgfile(args.fpg_file)
        
        logger.info("Successfully connected to FPGA")
    except Exception as e:
        logger.error(f"Failed to connect to FPGA: {str(e)}")
        sys.exit(1)
    
    # Main monitoring loop
    snapshot_count = 0
    
    try:
        while True:
            try:
                # Get ADC snapshot
                x, y = sparrow.get_adc_snapshot()
                snapshot_count += 1
                
                # Analyze snapshot
                metrics = analyze_adc_snapshot(x, y)
                
                # Log metrics
                logger.info(f"Snapshot #{snapshot_count}")
                logger.info(f"Power (Ch0): {metrics['power_ch0']:.2f}, Power (Ch1): {metrics['power_ch1']:.2f}")
                logger.info(f"Min/Max (Ch0): {metrics['min_ch0']}/{metrics['max_ch0']}, Min/Max (Ch1): {metrics['min_ch1']}/{metrics['max_ch1']}")
                logger.info(f"StdDev (Ch0): {metrics['std_ch0']:.2f}, StdDev (Ch1): {metrics['std_ch1']:.2f}")
                logger.info(f"Saturated samples (Ch0): {metrics['saturated_samples_ch0']} ({metrics['saturated_percent_ch0']:.2f}%)")
                logger.info(f"Saturated samples (Ch1): {metrics['saturated_samples_ch1']} ({metrics['saturated_percent_ch1']:.2f}%)")
                logger.info("-" * 40)
                
            except Exception as e:
                logger.error(f"Error getting ADC snapshot: {str(e)}")
            
            # Wait for next interval
            time.sleep(args.interval)
            
    except Exception as e:
        logger.error(f"Monitoring failed: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
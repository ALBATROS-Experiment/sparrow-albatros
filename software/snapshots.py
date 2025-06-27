#!/home/casper/python3-venv/bin/python


from sparrow_albatros import AlbatrosDigitizer
import casperfpga
import logging
import time
import numpy as np
import argparse
import matplotlib.pyplot as plt

# Init the logger, make it print to terminal
logger=logging.getLogger("my_logger")
logger.setLevel(logging.DEBUG)
console_handler=logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.debug("This is a debug message")

host="10.10.11.99"
fpgfile=None
cfpga=casperfpga.CasperFpga(host, transport=casperfpga.KatcpTransport)
s=AlbatrosDigitizer(cfpga,fpgfile,250,logger)
cfpga.get_system_information()


p0,p1 = s.get_adc_snapshot()

# Setup matplotlib for interactive plotting
plt.ion()
fig, (ax0, ax1) = plt.subplots(2, 1, figsize=(12, 8))
fig.suptitle('Snapshots')

ax0.set_title('Polarization 0')
ax0.set_xlabel('Time samples (1/250 MHz)')
ax0.set_ylabel('Voltage (ADC units)')
ax0.grid(True)

ax1.set_title('Polarization 1')
ax1.set_xlabel('Time samples (1/250 MHz)')
ax1.set_ylabel('Voltage (ADC units)')
ax1.grid(True)


# Create initial empty plots for both polarizations
line_pol0, = ax0.plot(p0, 'r-', label='pol0')
line_pol1, = ax1.plot(p1, 'b-', label='pol1')

# Update function
def update_plot(p0, p1):
    # Update line data
    line_pol0.set_ydata(p0/(1<<4))
    line_pol1.set_ydata(p1/(1<<4))
    # Adjust y-axis limits to show all data
    ax0.set_ylim(-(1<<11)-100, (1<<11) + 100)
    ax1.set_ylim(-(1<<11)-100, (1<<11) + 100)
    # Redraw the figure
    fig.canvas.draw()
    fig.canvas.flush_events()

# Main loop
while True:
    try:
        time.sleep(0.5)
        p0,p1 = s.get_adc_snapshot()
        
        update_plot(p0, p1)
        
    except KeyboardInterrupt:
        print("Plot updates stopped by user")
        plt.ioff()
        break
    except Exception as e:
        logger.error(f"Error in plotting loop: {e}")
        time.sleep(1)  # Prevent rapid error looping

from sparrow_albatros import AlbatrosDigitizer
import casperfpga
import logging
import time
import numpy as np
import argparse
import matplotlib.pyplot as plt

# Create the argument parser
parser = argparse.ArgumentParser(description="Process minfreq and maxfreq arguments")
# Add positional arguments for minfreq and maxfreq
parser.add_argument('minfreq', type=float, help='Minimum frequency (MHz)')
parser.add_argument('maxfreq', type=float, help='Maximum frequency (MHz)')
# Parse the arguments
args = parser.parse_args()
# Access the arguments
minfreq = args.minfreq
maxfreq = args.maxfreq
assert minfreq>=0, "Minfreq must be greater than zero"
assert maxfreq<=125, "Maxfreq must be lesser than 250 MHz"

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

# Setup matplotlib for interactive plotting
plt.ion()
fig, ax = plt.subplots(figsize=(12, 8))
ax.set_title('Power Spectrum')
ax.set_xlabel('Frequency (MHz)')
ax.set_ylabel('Power (dB)')
ax.grid(True)

# Create initial empty plots for both polarizations
idxs = np.arange(int(minfreq*2048/125), int(maxfreq*2048/125))
x_freq = np.linspace(minfreq, maxfreq, len(idxs))
line_pol00, = ax.plot(x_freq, np.zeros(len(idxs)), 'r-', label='pol00')
line_pol11, = ax.plot(x_freq, np.zeros(len(idxs)), 'b-', label='pol11')
ax.legend()

# Add vertical line and text for center channel
center_idx = len(idxs) // 2
center_freq = x_freq[center_idx]
vline = ax.axvline(x=center_freq, color='g', linestyle='--', alpha=0.7)
text_box = ax.text(center_freq, 0, f'ch{idxs[center_idx]}', 
                  horizontalalignment='center', verticalalignment='bottom',
                  bbox=dict(facecolor='white', alpha=0.7))

# Update function
def update_plot(pol00_data, pol11_data):
    # Calculate dB values
    pol00_db = 10 * np.log10(pol00_data)
    pol11_db = 10 * np.log10(pol11_data)
    
    # Update line data
    line_pol00.set_ydata(pol00_db)
    line_pol11.set_ydata(pol11_db)
    
    # Adjust y-axis limits to show all data
    min_val = min(np.min(pol00_db), np.min(pol11_db))
    max_val = max(np.max(pol00_db), np.max(pol11_db))
    padding = (max_val - min_val) * 0.1
    ax.set_ylim(min_val - padding, max_val + padding)
    
    # Update text box vertical position
    text_box.set_y(min_val - padding/2)
    
    # Redraw the figure
    fig.canvas.draw()
    fig.canvas.flush_events()

# Main loop
while True:
    try:
        time.sleep(0.5)
        pols = s.read_pols(["pol00", "pol11"])
        pol00, pol11 = pols["pol00"], pols["pol11"]
        
        update_plot(pol00[idxs], pol11[idxs])
        
    except KeyboardInterrupt:
        print("Plot updates stopped by user")
        plt.ioff()
        break
    except Exception as e:
        logger.error(f"Error in plotting loop: {e}")
        time.sleep(1)  # Prevent rapid error looping

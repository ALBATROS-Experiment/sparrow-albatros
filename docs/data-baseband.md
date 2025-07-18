# Baseband

- What is baseband?
- Specify the header format?
- Refer to how it's packetized (in the gateware design overview) and talk about the limitations this imposes on 1-bit the data. 
- Also data is read in multiples of four bytes over spi interface which limits flexibility in one-bit channels selectable. 
- How to read and plot the data, pointers to Albatros analysis repository. 
- Point out/document specific c-code that writes out the business. 

## Introduction to Baseband Data

Baseband data refers to the raw, digitized signal output from the ADCs after it has been processed through the PFB (Polyphase Filter Bank) and FFT (Fast Fourier Transform) stages, but before any correlation is performed. This data represents the complex frequency-domain representation of the original input signals from both polarizations.

In the Sparrow Albatros system, baseband data can be requantized to either 1-bit or 4-bit resolution before being packetized and transmitted over the network. This allows for flexible bandwidth usage depending on the scientific requirements of the observation.

## Data Collection Process

The baseband data flows through the following processing chain:

1. Analog signals are digitized by the ADCs at 250 MSPS
2. The digital samples are processed through the PFB/FFT pipeline
3. Data is requantized to either 1-bit or 4-bit resolution
4. Selected frequency channels are reordered and packetized
5. Packets are transmitted over UDP to a receiving computer
6. The `dump_baseband` utility captures these packets and writes them to disk

For details on the baseband data collection process see the [Embedded Software/Dumping Baseband](embedded/dump-baseband.md) page.

## Baseband Data Format

### Packetization and Limitations

As described in the [gateware design overview](gateware/gateware-design.md#packetiser), the baseband data is packetized in the FPGA before transmission. The packetization process imposes some limitations on the data, particularly for 1-bit mode:

- Data is bussified onto an 8-bit bus before packetization
- For 4-bit data (4 bits real + 4 bits imaginary for each polarization), this fundamentally limits us to 1024 of 2048 channels
- For 1-bit data, channels must be selected in multiples of four due to the SPI interface reading only in multiples of four bytes. Channels come in pairs starting with an even indexed channels because the gateware's 1-bit-data bussifier employs a barrel-switcher that pairs consecutive channels, further limiting the flexibility in channel selection.

### UDP Packet Format

Each UDP packet contains:
- A 4-byte spectrum number (specno) header
- Multiple spectra of baseband data (the number of spectra per packet is configurable)

The number of spectra per packet is calculated to optimize data transfer, with a maximum of 30 spectra per packet. This is determined by the `get_nspec` function in the `dump_baseband` utility:

```c
uint64_t get_nspec(uint64_t bytes_per_spec, uint64_t max_nbyte) {
    uint64_t nspec = max_nbyte / bytes_per_spec; 
    if (nspec > 30) {
        nspec = 30;
    } else if (nspec < 1) {
        log_message("WARNING: nspec<1, packets may be fragmented.\n");
        nspec = 1;
    }
    return nspec;
}
```

### Raw File Header Format

When baseband data is captured to disk, a comprehensive header is written to the start of each file. The header includes:

1. Header size information
2. Version information
3. Packet and spectral metadata
4. GPS timing and location data (if available)
5. Channel indices
6. Digital gain coefficients for both polarizations

The header is written in big-endian format to ensure cross-platform compatibility:

```c
uint64_t file_header0[FH0SIZE] = {
    to_big_endian(header_bytes),     // The number of bytes in the header
    to_big_endian(escape_seq_zero),  // Escape sequence to distinguish from old format
    to_big_endian(version_major),    // Major version number
    to_big_endian(version_minor),    // Minor version number
    to_big_endian(bytes_per_packet), // Number of bytes in each UDP packet payload
    to_big_endian(lenchans),         // Number of frequency channels
    to_big_endian(spec_per_packet),  // Number of spectra per packet
    to_big_endian(bits),             // Quantization bits (1 or 4)
    to_big_endian(adc_clk),          // ADC sampling rate in MHz
    to_big_endian(fft_framelen),     // FFT frame size
    to_big_endian(station_id),       // Station ID
    to_big_endian(have_gps),         // Flag indicating if GPS data is available
    to_big_endian(time_s),           // Unix timestamp (seconds)
    to_big_endian(time_ns),          // Nanosecond precision
    to_big_endian_double(lattitude), // Latitude in degrees
    to_big_endian_double(longitude), // Longitude in degrees
    to_big_endian_double(elevation), // Altitude in meters
};
```

Following this initial header section, the file contains:
- Channel indices for each selected channel
- Digital gain coefficients for polarization 0
- Digital gain coefficients for polarization 1
- The actual baseband data packets

## Capturing Baseband Data

The Sparrow Albatros system provides a dedicated C utility, `dump_baseband`, to capture the UDP packets containing baseband data and write them to disk. This utility is optimized for high-throughput data capture with minimal packet loss.

### Configuration

The `dump_baseband` utility reads its configuration from a standard INI file (typically `config.ini`). Important configuration parameters include:

```ini
[baseband]
channels=190:194 220:222  # Format: range1 range2 ...
file_size=1               # Size in GB
bits=4                    # 1 for 1-bit mode, 4 for 4-bit mode
version_major=1           # Header version
version_minor=0           # Header version

[paths]
dump_baseband_output_directory=/path/to/output
coeffs_pol0_binary_path=/path/to/coeffs0
coeffs_pol1_binary_path=/path/to/coeffs1

[networking]
max_bytes_per_packet=8192  # Maximum UDP payload size
```

### Implementation Details

The utility uses the libpcap library to capture network packets matching specific filter criteria:

```c
char filter_exp[] = "udp and dst port 7417 and dst host 10.10.11.99 and src host 192.168.41.10";
```

Files are organized into directories named by timestamp slice to facilitate data management. Each raw file contains:
1. The header as described above
2. A sequence of UDP packet payloads containing the baseband data

The utility monitors for packet loss both within individual files and between consecutive files, logging statistics to help identify data quality issues.

## Reading and Analyzing Baseband Data

To read and analyze the baseband data, refer to the [Albatros Analysis](https://github.com/ALBATROS-Experiment/albatros_analysis) repository, which provides Python utilities for:

1. Reading the raw file format
2. Extracting and interpreting the header information
3. Processing the baseband data
4. Plotting and visualizing the data

The header information can be loaded and parsed to understand the data parameters, and the actual data can be processed for scientific analysis.

## C Code Implementation

The implementation of the `dump_baseband` utility is found in `software/dump_baseband.c`. Key functions include:

- `write_header`: Writes the comprehensive file header
- `get_config_from_ini`: Parses the INI configuration file
- `get_packets_per_file`: Calculates how many packets to write per file
- `parse_chans`: Parses channel specifications from the configuration
- `set_coeffs_from_serialized_binary_files`: Loads digital gain coefficients

The main capture loop in the utility captures packets, extracts the payload, and writes them sequentially to disk, organizing files by timestamp.


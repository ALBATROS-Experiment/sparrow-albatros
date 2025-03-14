#include <pcap.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <arpa/inet.h>
#include <time.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <arpa/inet.h> // for ntohl network to host long
#include "ini.h" // Ensure inih is installed
#include "dump_baseband.h"

// Parse chans in config.ini format (e.g. "chans=190:194 220:222" means [190,191,192,193,220,221])
// TODO: Fix this! (done?)
void parse_chans(const char* chans_string, config_t* config) {
    // Count the number of ranges (space-separated)
    char* chans_strcpy = strdup(chans_string); // Copy input string to avoid modifying it
    char* token = strtok(chans_strcpy, " ");
    size_t count = 0;
    while (token != NULL) {
        char* colon = strchr(token, ':');
        if (colon != NULL) {
            uint64_t start = strtoull(token, NULL, 10);
            uint64_t end = strtoull(colon + 1, NULL, 10);
            count += (end - start); // Add size of range
        }
        token = strtok(NULL, " ");
    }
    free(chans_strcpy);
    // Allocate memory for chans (and coeffs, because they're going to be the same)
    config->chans = (uint64_t*)malloc(count * sizeof(uint64_t));
    config->coeffs_pol0 = (uint64_t*)malloc(count * sizeof(uint64_t));
    config->coeffs_pol1 = (uint64_t*)malloc(count * sizeof(uint64_t));
    config->lenchans = (uint64_t)count;
    // Parse the string again to fill chans
    chans_strcpy = strdup(chans_string); // deep copy
    token = strtok(chans_strcpy, " "); // split chans_strcpy into tokens, returns pointer to next token on subsequent calls
    // Loop to fill chans array with data based on chans_string
    size_t index = 0;
    while (token != NULL) {
        char* colon = strchr(token, ':');
        if (colon != NULL) {
            uint64_t start = strtoull(token, NULL, 10);
            uint64_t end = strtoull(colon + 1, NULL, 10);
            for (uint64_t i = start; i < end; i++) {
                config->chans[index++] = i; 
            }
        }
        token = strtok(NULL, " ");
    }
    free(chans_strcpy);
}

// Callback function for parsing the ini file
static int my_ini_handler(void* user, const char* section, const char* name, const char* value) {
    config_t* pconfig = (config_t*)user; // Init a config_t structure variable; this struct is defined in header file
    if (strcmp(section, "baseband") == 0) {
        if (strcmp(name, "channels") == 0) {
            parse_chans(value, pconfig); // Use custom parser for chans, also defines lenchans
        } else if (strcmp(name, "file_size") == 0) {
            pconfig->file_size = strtod(value, NULL); // string to double
        } else if (strcmp(name, "bits") == 0) {
            pconfig->bits = strtoul(value, NULL, 10);
        } else if (strcmp(name, "version_major") == 0) {
            pconfig->version_major = strtoul(value, NULL, 10);
        } else if (strcmp(name, "version_minor") == 0) {
            pconfig->version_minor = strtoul(value, NULL, 10);
        }
    } else if (strcmp(section, "paths") == 0) {
        if (strcmp(name, "dump_spectra_output_directory") == 0) {
            strncpy(pconfig->dump_spectra_output_directory, value, sizeof(pconfig->dump_spectra_output_directory) - 1);
            pconfig->dump_spectra_output_directory[sizeof(pconfig->dump_spectra_output_directory) - 1] = '\0';
        } else if (strcmp(name, "dump_baseband_output_directory") == 0) {
            strncpy(pconfig->dump_baseband_output_directory, value, sizeof(pconfig->dump_baseband_output_directory) - 1);
            pconfig->dump_baseband_output_directory[sizeof(pconfig->dump_baseband_output_directory) - 1] = '\0';
        } else if (strcmp(name, "log_directory") == 0) {
            strncpy(pconfig->log_directory, value, sizeof(pconfig->log_directory) - 1);
            pconfig->log_directory[sizeof(pconfig->log_directory) - 1] = '\0';
        } else if (strcmp(name, "coeffs_pol0_binary_path") == 0) {
            strncpy(pconfig->coeffs_pol0_binary_path, value, sizeof(pconfig->coeffs_pol0_binary_path) - 1);
            pconfig->coeffs_pol0_binary_path[sizeof(pconfig->coeffs_pol0_binary_path) - 1] = '\0';
        } else if (strcmp(name, "coeffs_pol1_binary_path") == 0) {
            strncpy(pconfig->coeffs_pol1_binary_path, value, sizeof(pconfig->coeffs_pol1_binary_path) - 1);
            pconfig->coeffs_pol1_binary_path[sizeof(pconfig->coeffs_pol1_binary_path) - 1] = '\0';
        }
    } else if (strcmp(section, "networking") == 0) {
        if (strcmp(name, "max_bytes_per_packet") == 0) {
            pconfig->max_bytes_per_packet = strtoul(value, NULL, 10);
        }
    }
    return 1; // Continue parsing
}

// Read a binary file into an array
// This function is made for reading coeffs into binary array
int read_binary_file_into_array(char* binary_path, uint64_t* array, uint64_t n_elements_in_file) {
    // Open a file
    FILE *file = fopen(binary_path, "rb"); // binary_path must be null terminated
    if (file == NULL) {
        perror("Error opening file");
        return 1;
    }
    // Move to the end of the file to determine its size
    fseek(file, 0, SEEK_END);
    long file_size = ftell(file);
    rewind(file);
    if (file_size < 0) {
        perror("Failed to get file size");
        fclose(file);
        return 1;
    }
    // Ensure the file size (in bytes) is a multiple of sizeof(uint64_t)
    if (file_size % sizeof(uint64_t) != 0) {
        fprintf(stderr, "File size is not a multiple of uint64_t\n");
        fclose(file);
        return 1;
    }
    // Calculate the number of uint64_t elements
    size_t num_elements = file_size / sizeof(uint64_t);
    // Ensure num_elements corresponds to n_elements_in_file
    if ((uint64_t)num_elements != n_elements_in_file) {
        printf("num_elements read: %d\n", num_elements);
        printf("num elements expected: %d\n", (int)n_elements_in_file);
        perror("Number of elements found does not match expectation\n");
        fclose(file);
        return 1;
    }
    // Memory has already been allocated
    // Read the entire file into the array
    size_t read_elements = fread(array, sizeof(uint64_t), num_elements, file);
    if (read_elements != num_elements) {
        perror("Failed to read file");
        fclose(file);
        return 1;
    }
    fclose(file);
    return 0;
}

// Read a binary file of the coefficients into coefficients array
int set_coeffs_from_serialized_binary_files(config_t* pconfig) {
    int retval = read_binary_file_into_array(pconfig->coeffs_pol0_binary_path, pconfig->coeffs_pol0, pconfig->lenchans);
    if (retval == 1) { return 1; }
    retval = read_binary_file_into_array(pconfig->coeffs_pol1_binary_path, pconfig->coeffs_pol1, pconfig->lenchans);
    return retval;
}

//// Read a binary file, the location of which is provided by the config_t struct
//// Set coeffients based on data read and make pconfig->coeffs point to it
//int set_coeffs_from_serialized_binary_files(config_t* pconfig) {
//    FILE *file = fopen(pconfig->coeffs_binary_path, "rb");
//    if (file == NULL) {
//        perror("Error opening file");
//        return 1;
//    }
//    // Move to the end of the file to determine its size
//    fseek(file, 0, SEEK_END);
//    long file_size = ftell(file);
//    rewind(file);
//    if (file_size < 0) {
//        perror("Failed to get file size");
//        fclose(file);
//        return 1;
//    }
//    // Ensure the file size is a multiple of uint64_t
//    if (file_size % sizeof(uint64_t) != 0) {
//        fprintf(stderr, "File size is not a multiple of uint64_t\n");
//        fclose(file);
//        return 1;
//    }
//    // Calculate the number of uint64_t elements
//    size_t num_elements = file_size / sizeof(uint64_t);
//    // Ensure num_elements corresopnds to lenchans
//    if ((uint64_t)num_elements != pconfig->lenchans) {
//        printf("num_elements: %d\n", num_elements);
//        printf("lenchans: %d\n", (int)pconfig->lenchans);
//        perror("Number of elements in serialized coeffs file does not match lenchans\n");
//        fclose(file);
//        return 1;
//    }
//    // Memory has already been allocated
//    // Read the entire file into the array
//    size_t read_elements = fread(pconfig->coeffs_pol0, sizeof(uint64_t), num_elements, file);
//    if (read_elements != num_elements) {
//        perror("Failed to read file");
//        fclose(file);
//        return 1;
//    }
//    fclose(file);
//    // deep copy elements from pconfig->coeffs_pol0 into pconfig->coeffs_pol1
//    memcpy(pconfig->coeffs_pol1, pconfig->coeffs_pol0, num_elements * sizeof(uint64_t));
//    // TODO: make it so that digital gain coefficients are computed independently
//    return 0;
//}


// Needs to yield same result as function get_nspec in utils.py 
uint64_t get_nspec(uint64_t bytes_per_spec, uint64_t max_nbyte) {
    uint64_t nspec = max_nbyte / bytes_per_spec; 
    if (nspec > 30) {
        nspec = 30;
    } else if (nspec < 1) {
        printf("WARNING: nspec<1, packets may be fragmented.");
        nspec = 1;
    }
    return nspec;
}

// Read .ini configuration file and populate config_t struct variable with it's contents
config_t get_config_from_ini(const char* filename) {
    config_t config;
    // Initialize pointers to NULL before allocation
    config.chans = NULL;
    config.coeffs_pol0 = NULL;
    config.coeffs_pol1 = NULL;
    // Parse the INI file
    if (ini_parse(filename, my_ini_handler, &config) < 0) {
        printf("Can't load config.ini\n");
        exit(1);
    }
    // coeffs memory has already been allocated,
    if (set_coeffs_from_serialized_binary_files(&config) != 0) {
        printf("Can't load coeffs from serialized binary.\n");
        exit(1);
    }
    config.bytes_per_specnum = 4;
    if (config.bits==4) {
    	config.bytes_per_spec = config.lenchans * 2;
    } else if (config.bits==1) {
    	config.bytes_per_spec = config.lenchans / 2; // must be even, starting with even indices
    }
    config.spec_per_packet = get_nspec(config.bytes_per_spec, config.max_bytes_per_packet);
    config.bytes_per_packet = (config.spec_per_packet * config.bytes_per_spec) + config.bytes_per_specnum;
    printf("bytes_per_spec: %d\n", (int)config.bytes_per_spec);
    printf("spec_per_packet: %d\n", (int)config.spec_per_packet);
    printf("bytes_per_packet: %d\n", (int)config.bytes_per_packet);
    return config;
}

// Flip the endiannes of a uint64_t 
uint64_t to_big_endian(uint64_t value) {
    uint64_t result =
        ((value & 0x00000000000000FF) << 56) |
        ((value & 0x000000000000FF00) << 40) |
        ((value & 0x0000000000FF0000) << 24) |
        ((value & 0x00000000FF000000) << 8)  |
        ((value & 0x000000FF00000000) >> 8)  |
        ((value & 0x0000FF0000000000) >> 24) |
        ((value & 0x00FF000000000000) >> 40) |
        ((value & 0xFF00000000000000) >> 56);
    return result;
}

// Flip the endianness of a double
double to_big_endian_double(double value) {
    uint64_t temp = *(uint64_t*)&value; // Reinterpret as double 
    uint64_t result = to_big_endian(temp); // to big endian
    return *(double*)&result; // Cast the result back to double
}


// Specifies the format and writes the header of an open, binary file
size_t write_header(FILE *file, uint64_t *chans, uint64_t *coeffs_pol0, uint64_t *coeffs_pol1, uint64_t version_major, uint64_t version_minor, uint64_t lenchans, uint64_t spec_per_packet, uint64_t bytes_per_packet, uint64_t bits) {
    #define FH0SIZE 17
    // Total number of bytes in header, including bytes for header_bytes
    uint64_t header_bytes = (FH0SIZE + 3 * lenchans) * sizeof(uint64_t); // 1xlenchans for chans (idxs), 2xlenchans for coeffs
    uint64_t escape_seq_zero = 0; // escape sequence to distinguish versioned headers from legacy header (SNAP data)
    // TODO: Version number is hard coded, major minor
    uint64_t adc_clk = 250; // ADC sample rate MHz. TODO: read this from config.ini  [baseband] -> adc_clk
    uint64_t fft_framelen = 4096; // Size of frames input into FFT on FPGA. TODO: get this from .fpg file instead
    uint64_t station_id = 0; // The station id. Defaults to 0. TODO: establish convention and read from config.ini 
    // TODO: Read LeoBodnar (for now we use dummy)
    uint64_t have_gps  = 0; // bool, 1-true, 0-false
    uint64_t gps_week  = 0; // This is set to zero for whatever reason
    uint64_t time_s    = 0; // IRL read GPS or RTC time with lbtools
    uint64_t time_ns   = 0; // IRL read GPS or RTC time with lbtools
    uint64_t lattitude = 0; // IRL read GPS loc with lbtools
    uint64_t longitude = 0; // IRL read GPS loc with lbtools
    uint64_t elevation = 0; // IRL read GPS loc with lbtools
    size_t header_bytes_written = 0; // A number we increment and then compare with header_bytes
    uint64_t file_header0[FH0SIZE] = {
        to_big_endian(header_bytes),     // 1, the number of bytes in the header including the bytes in header_bytes
        to_big_endian(escape_seq_zero),  // 2, Escape sequence (zeros), to distinguish from old format without version number
        to_big_endian(version_major),    // 3, the major version number of the header 
        to_big_endian(version_minor),    // 4, minor version number
        to_big_endian(bytes_per_packet), // 5, the nuber of bytes in the payload of each UDP packet
        to_big_endian(lenchans),         // 6, number of frequency channels, both hardware channels 
        to_big_endian(spec_per_packet),  // 7, number of spectra per packet
        to_big_endian(bits),             // 8, number of bits quantized 1 or 4
        to_big_endian(adc_clk),          // 9, ADC sampling rate in MHz
        to_big_endian(fft_framelen),     // 10, FFT frame size, number of time-domain samples going into each FFT
        to_big_endian(station_id),       // 11, station ID, read from config.ini, can default to 0
        to_big_endian(have_gps),         // 12, binary whether there is a GPS
        to_big_endian(time_s),           // 13, The time (ctime) in seconds
        to_big_endian(time_ns),          // 14, The time (ctime) in nano-seconds, can default to 0
        to_big_endian_double(lattitude), // 15
        to_big_endian_double(longitude), // 16
        to_big_endian_double(elevation), // 17
    };
    size_t elements_written = fwrite(file_header0, sizeof(uint64_t), FH0SIZE, file);
    if (elements_written != FH0SIZE) {
        perror("Error writing header-preamble to file");
    }
    #undef FH0SIZE
    header_bytes_written += elements_written * sizeof(double);
    // Write channels that are used 
    for (int i=0; i<(int)lenchans; i++) {
        uint64_t big_endian_coeff = to_big_endian(chans[i]);
        header_bytes_written += fwrite(&big_endian_coeff, sizeof(uint64_t), 1, file) * sizeof(uint64_t);
    } 
    // Write the digital gain coefficients in each channel
    for (int i=0; i<(int)lenchans; i++) {
        uint64_t big_endian_coeff = to_big_endian(coeffs_pol0[i]);
        header_bytes_written += fwrite(&big_endian_coeff, sizeof(uint64_t), 1, file) * sizeof(uint64_t);
    }
    for (int i=0; i<(int)lenchans; i++) {
        uint64_t big_endian_coeff = to_big_endian(coeffs_pol1[i]);
        header_bytes_written += fwrite(&big_endian_coeff, sizeof(uint64_t), 1, file) * sizeof(uint64_t);
    }
    // Compare the actual number of bytes written with how much we said we would write in header_bytes as a precaution
    if (header_bytes_written != (size_t)header_bytes) {
        fprintf(stderr, "Error! Header bytes was not correctly computed, expected %d instead go %d\n", (int)header_bytes, (int)header_bytes_written);
    }
    return header_bytes_written;
}

// Helper to compute number of UDP packets needed to achieve desired file size
int get_packets_per_file(config_t* config) {
    double file_size_bytes = 1024 * 1024 * 1024 * config->file_size; // double
    // To get the header size, we hack write_header_file and make sure everything is alright
    FILE *null_file = fopen("/dev/null","wb");
    if (null_file == NULL) return -1;
    size_t header_bytes = write_header(null_file, config->chans, config->coeffs_pol0, config->coeffs_pol1, config->version_major, config->version_minor, config->lenchans, config->spec_per_packet, config->bytes_per_packet, config->bits);
    fclose(null_file);
    int n_packets_per_file = ((int)file_size_bytes - (int)header_bytes) / (int)config->bytes_per_packet;
    // config->bytes_per_packet is uint64
    return n_packets_per_file;
}

// Checks if a directory exists at specified path, if not try to create one 
int create_directory_if_not_exists(char* path) {
    struct stat st = {0};
    // Check if the directory exists
    if (stat(path, &st) == -1) {
        // Directory doesn't exist, create it
        if (mkdir(path, 0777) == 0) {
            printf("Directory created successfully: %s\n", path);
            return 0;
        } else {
            perror("Failed to create directory\n");
            return -1;
        }
    } else {
        printf("Directory already exists: %s\n", path);
        return 1;
    }
}

int main() {
    char errbuf[PCAP_ERRBUF_SIZE];
    pcap_t *handle;
    struct bpf_program fp; // The compiled filter
    char filter_exp[] = "udp and dst port 7417 and dst host 10.10.11.99 and src host 192.168.41.10";
    bpf_u_int32 net;
    
    /////////////////// INIT PACKET SNIFFER ///////////////////
    // Create sniffing device
    handle = pcap_create("eth0", errbuf);
    if (handle == NULL) {
        fprintf(stderr, "Couldn't open device: %s\n", errbuf);
        return 1;
    }
    // Promiscuous mode
    if (pcap_set_promisc(handle, 1) != 0) {
        fprintf(stderr, "Couldn't set promiscuous mode: %s\n", pcap_geterr(handle));
        return 1;
    }
    // Set timeout
    if (pcap_set_timeout(handle, 1000) !=  0) {
        fprintf(stderr, "Couldn't set timeout: %s\n", pcap_geterr(handle));
        return 1;
    }
    // Set buffer size to 20 MB 20*1024*1024=20971520 bytes
    if (pcap_set_buffer_size(handle, 20971520) != 0) {
        fprintf(stderr, "Couldn't set buffer size: %s\n", pcap_geterr(handle));
        return 1;
    }
    if (pcap_set_snaplen(handle, BUFSIZ) != 0) {
        fprintf(stderr, "Couldn't set snap buffer: %s\n", pcap_geterr(handle));
        return 1;
    }
    // Activate
    if (pcap_activate(handle) != 0) {
        fprintf(stderr, "Couldn't activate pcap handle: %s\n", pcap_geterr(handle));
        return 1;
    }
    // Compile the filter expression
    if (pcap_compile(handle, &fp, filter_exp, 0, net) == -1) {
        fprintf(stderr, "Couldn't parse filter %s: %s\n", filter_exp, pcap_geterr(handle));
        return 1;
    }
    // Set the compiled filter
    if (pcap_setfilter(handle, &fp) == -1) {
        fprintf(stderr, "Couldn't install filter %s: %s\n", filter_exp, pcap_geterr(handle));
        return 1;
    }

    /////////////////// LOAD CONFIG FOR HEADER AND GET METADATA ///////////////////
    // Parse config.ini
    config_t config = get_config_from_ini(CONFIGINI_PATH);
    // Get coeffs
    // TODO: get coefficients from file
    // TODO: Figure out how much space there is on drive
    // TODO: Figure out how many files we can write to this drive based on how much space there 
    // is on drive, the size of each file, and the drive safety parameter which sets the maximum
    // fullness of the drives
    int n_files_to_write = 50000; // dummy
    int packets_per_file = get_packets_per_file(&config); // Figure out how many packets to write per file
    // TODO: log pertinant information
    // TODO: figure out how to deal with muxing drives, whether to do that in C or have a supervisor bash/python script for this
    printf("packets_per_file: %d\n", packets_per_file);
    uint32_t specno_end_prev_file = 0;

    // Loop through number of packets to write (this is the main loop)
    for (int i = 0; i < n_files_to_write; i++) {
        // Create directory if it doesn't exist
        char timestamp[20]; // big enough to hold the timestamp as a string
        time_t raw_time;
        raw_time = time(NULL); // Get current time
        snprintf(timestamp, sizeof(timestamp), "%ld", (long)raw_time); // Convert the time to a string, typecase (long) gives seconds
        char sliced_timestamp[6]; // Slice of first 5 chars (+1 for null pointer) of ctime timestamp
        strncpy(sliced_timestamp, timestamp, 5);
        sliced_timestamp[5] = '\0'; // Set null pointer at end of array
        char bbfiledir[MAX_STRING_LENGTH + MAX_STRING_LENGTH]; // five digit directory, create if DNE
        snprintf(bbfiledir, sizeof(bbfiledir), "%s/%s", config.dump_baseband_output_directory, sliced_timestamp);
        int create_dir_result = create_directory_if_not_exists(bbfiledir);
        if (create_dir_result == -1) return 1;

        // Open a binary file to write
        char bbfilepath[MAX_STRING_LENGTH + MAX_STRING_LENGTH];
        snprintf(bbfilepath, sizeof(bbfilepath), "%s/%s/%s.raw", config.dump_baseband_output_directory, sliced_timestamp, timestamp);
        FILE *file = fopen(bbfilepath, "wb");
        printf("Writing to %s\n", bbfilepath);
        if (file == NULL) {
            perror("Error opening file");
            return 1;
        }

        // Set the buffer size to 20 MB (file write buffer)
        size_t buffer_size = 20 * 1024 * 1024;
        char *buffer = malloc(buffer_size); // Allocate buffer
        if (setvbuf(file, buffer, _IOFBF, buffer_size) != 0) {
            perror("Error setting buffer");
            return 1;
        }

        // Write the binary file header
        size_t header_bytes = write_header(file, config.chans, config.coeffs_pol0, config.coeffs_pol1, config.version_major, config.version_minor, config.lenchans, config.spec_per_packet, config.bytes_per_packet, config.bits);

        // Capture and write packets_per_file packets
        uint32_t specno_start;
        uint32_t specno_end;
        for (int i = 0; i < packets_per_file; i++) {
            struct pcap_pkthdr header;
            const u_char *packet = pcap_next(handle, &header);
            if (packet == NULL) {
                printf("Failed to capture a packet\n");
                return 1;
            }
            //printf("Captured a packet with length: %d\n", header.len);
            // Parse the packet, assumes eth0 traffic already filtered correctly (only accept UDP packets from FPGA going to Sparrow IP)
            // Write the packet to the binary file, use pointer arithmetic to seek payload starting point
            if (i == 0) {
                memcpy(&specno_start, packet + UDP_PAYLOAD_START, sizeof(uint32_t));
                specno_start = ntohl(specno_start);
            } else if (i == packets_per_file - 1) {
                memcpy(&specno_end, packet + UDP_PAYLOAD_START, sizeof(uint32_t));
                specno_end = ntohl(specno_end);
            }
            size_t bytes_written = fwrite(packet + UDP_PAYLOAD_START, 1, (size_t)config.bytes_per_packet, file);
            if (bytes_written != (size_t)config.bytes_per_packet) {
                fprintf(stderr, "Failed to write all bytes to file\n");
            }
        }
        printf("Dropped packets within file %.8f%%\n", 100 - (100 * ((double)config.spec_per_packet * (double)packets_per_file) / ((double)specno_end - (double)specno_start + (double)config.spec_per_packet)));
        printf("Dropped packets between files %.2f\n", ((double)specno_start - ((double)specno_end_prev_file + (double)config.spec_per_packet)) / (double)config.spec_per_packet);
        //printf("specno_end_prev_file %d\n", specno_end_prev_file);
        //printf("specno_start %d\n", specno_start);
        //printf("specno_end %d\n", specno_end);
        specno_end_prev_file = specno_end;
        fclose(file);       // Close the file
        free(buffer);       // Clean up mallocated file-buffer space
    }
    // Cleanup
    pcap_freecode(&fp); // Free the compiled filter
    pcap_close(handle); // Close the handle
    return 0;
}















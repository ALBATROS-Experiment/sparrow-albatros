#define IP_HEADER_START 14 // Safe to assume for Ethernet, but not other link layers
#define UDP_HEADER_START (IP_HEADER_START + 20) // 20 bytes is the smallest IPV4 header size
#define UDP_PAYLOAD_START (UDP_HEADER_START + 8) // UDP header is always 8 bytes

#define DEST_IP "10.10.11.99"
#define DEST_PRT 7417
#define FILE_SIZE 0.5
#define HOST "10.10.11.99"
#define MAX_BYTES_PER_PACKET 1600
#define CHANNELS_STRING "200:240"
#define BITS 4
#define CONFIGINI_PATH "/home/casper/sparrow-albatros/software/config.ini"
#define MAX_STRING_LENGTH 256 // Define a reasonable limit for strings


// Struct for things to parse from config.ini plus derived quantities plus digital 
// gain coefficients. Much is to be written to the binary baseband file header
typedef struct {
    uint64_t* chans;
    uint64_t* coeffs_pol0;
    uint64_t* coeffs_pol1;
    uint64_t lenchans;
    uint64_t spec_per_packet;
    uint64_t bytes_per_specnum;
    uint64_t bytes_per_spec;
    uint64_t bytes_per_payload_specnum;
    uint64_t bytes_per_packet;
    uint64_t bits;
    char dump_spectra_output_directory[MAX_STRING_LENGTH];
    char dump_baseband_output_directory[MAX_STRING_LENGTH];
    char log_directory[MAX_STRING_LENGTH];
    char coeffs_pol0_binary_path[MAX_STRING_LENGTH];
    char coeffs_pol1_binary_path[MAX_STRING_LENGTH];
    double file_size;
    uint64_t max_bytes_per_packet;
    uint64_t version_major;
    uint64_t version_minor;
} config_t;


// Parse string to determine what frequency channels are being sent
void parse_chans(const char* chans_string, config_t* config);

// Handles parsing of .ini configuration file
static int my_ini_handler(void* user, const char* section, const char* name, const char* value);

// Read binary file specified at path given by config_t struct variable 
// containing digital gain coefficients, stores these in this same struct
int set_coeffs_from_serialized_binary_files(config_t* pconfig);

uint64_t get_nspec(uint64_t lenchans, uint64_t max_nbyte);

// Parse .ini configuration, derive some other quantities, return those in config_t struct variable
config_t get_config_from_ini(const char* filename);

// Flip the endianness of 64-bit primitives
uint64_t to_big_endian(uint64_t value);
double to_big_endian_double(double value);

// Write header of binary file that stores our baseband data
size_t write_header(FILE *file, uint64_t *chans, uint64_t *coeffs_pol0, uint64_t *coeffs_pol1, uint64_t version_major, uint64_t version_minor, uint64_t lenchans, uint64_t spec_per_packet, uint64_t bytes_per_packet, uint64_t bits);

// Figure out how many packets to write to each binary file
int get_packets_per_file(config_t* config);

// Create a directory at specified path if one doesn't exist already
int create_directory_if_not_exists(char* path);

// Helper for reading coeffs from serialize 4-bit coeffs
int read_binary_file_into_array(char* binary_path, uint64_t* array, uint64_t n_elements_in_file);





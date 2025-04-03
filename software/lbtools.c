#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <libusb-1.0/libusb.h>
#include <unistd.h>
#include <stdint.h>
#include <stdbool.h>

// Leo Bodnar USB device constants
#define VENDOR_LB 0x1DD2      // Leo Bodnar's Vendor ID
#define PRODUCT_MGPS 0x2211   // Mini GPS product ID
#define CONFIGURATION_MGPS 0  // 1-based
#define INTERFACE_MGPS 0      // 0-based
#define SETTING_MGPS 0        // 0-based
#define ENDPOINT_MGPS 0       // 0-based

// Function prototypes
bool usb_safe_cleanup(libusb_device_handle *dev, int interface);
bool lb_set(void);
bool lb_read(int ntry, int timeout, time_t *tstamp, double *nano, char *validity, 
             double *lon, double *lat, double *alt, struct tm *gpstime);
bool set_clock_lb(int current_year);

// Helper function for USB cleanup
bool usb_safe_cleanup(libusb_device_handle *dev, int interface) {
    bool status = true;
    
    try_release:
    if (libusb_release_interface(dev, interface) != 0) {
        printf("Failure in usb_safe_cleanup: could not release interface\n");
        status = false;
    }
    
    if (dev != NULL) {
        libusb_close(dev);
    }
    
    return status;
}

// Set Leo Bodnar into mode where it reports nav-data packets
bool lb_set(void) {
    bool status = false;
    libusb_device_handle *dev = NULL;
    libusb_device *device = NULL;
    struct libusb_config_descriptor *config = NULL;
    const struct libusb_interface *interface_desc = NULL;
    const struct libusb_interface_descriptor *setting = NULL;
    const struct libusb_endpoint_descriptor *endpoint = NULL;
    int ret;
    
    // Magic command to set the LB, courtesy of Simon
    unsigned char buffer[8] = {8, 6, 1, 8, 0, 0x01, 0x07, 10};
    
    // Initialize libusb
    ret = libusb_init(NULL);
    if (ret < 0) {
        printf("lb_set: failed to initialize libusb\n");
        return status;
    }
    
    // Find the USB device
    dev = libusb_open_device_with_vid_pid(NULL, VENDOR_LB, PRODUCT_MGPS);
    if (dev == NULL) {
        printf("lb_set: failed to find USB device\n");
        libusb_exit(NULL);
        return status;
    }
    
    // Get the device
    device = libusb_get_device(dev);
    
    // Reset the device
    ret = libusb_reset_device(dev);
    if (ret != 0) {
        printf("lb_set: failed to reset device\n");
        libusb_close(dev);
        libusb_exit(NULL);
        return status;
    }
    
    // Check for kernel driver (Linux only)
    #ifdef __linux__
    if (libusb_kernel_driver_active(dev, INTERFACE_MGPS)) {
        ret = libusb_detach_kernel_driver(dev, INTERFACE_MGPS);
        if (ret != 0) {
            printf("lb_set: failed to detach kernel driver\n");
            libusb_close(dev);
            libusb_exit(NULL);
            return status;
        }
    }
    #endif
    
    // Get configuration descriptor
    ret = libusb_get_config_descriptor(device, CONFIGURATION_MGPS, &config);
    if (ret != 0) {
        printf("lb_set: failed to get configuration descriptor\n");
        libusb_close(dev);
        libusb_exit(NULL);
        return status;
    }
    
    // Claim interface
    ret = libusb_claim_interface(dev, INTERFACE_MGPS);
    if (ret != 0) {
        printf("lb_set: failed to claim interface\n");
        libusb_free_config_descriptor(config);
        libusb_close(dev);
        libusb_exit(NULL);
        return status;
    }
    
    // Set configuration if necessary
    int current_config;
    ret = libusb_get_configuration(dev, &current_config);
    if (ret != 0 || current_config != CONFIGURATION_MGPS + 1) {
        ret = libusb_set_configuration(dev, CONFIGURATION_MGPS + 1);
        if (ret != 0) {
            printf("lb_set: failed to set configuration\n");
            usb_safe_cleanup(dev, INTERFACE_MGPS);
            libusb_free_config_descriptor(config);
            libusb_exit(NULL);
            return status;
        }
    }
    
    // Send control transfer
    ret = libusb_control_transfer(dev, 0x21, 9, 0x0300, 0, buffer, 8, 1000);
    if (ret != 8) {
        printf("lb_set: failed to write to device\n");
        usb_safe_cleanup(dev, INTERFACE_MGPS);
        libusb_free_config_descriptor(config);
        libusb_exit(NULL);
        return status;
    }
    
    // Cleanup
    usb_safe_cleanup(dev, INTERFACE_MGPS);
    libusb_free_config_descriptor(config);
    libusb_exit(NULL);
    status = true;
    return status;
}

// Read GPS time stamp from Leo Bodnar
bool lb_read(int ntry, int timeout, time_t *tstamp, double *nano, char *validity,
             double *lon, double *lat, double *alt, struct tm *gpstime) {
    bool status = false;
    libusb_device_handle *dev = NULL;
    libusb_device *device = NULL;
    struct libusb_config_descriptor *config = NULL;
    int ret, i, j;
    
    // Default ntry and timeout values if not specified
    if (ntry <= 0) ntry = 1000;
    if (timeout <= 0) timeout = 1000;
    
    // Initialize libusb
    ret = libusb_init(NULL);
    if (ret < 0) {
        printf("lb_read: failed to initialize libusb\n");
        return status;
    }
    
    // Find the USB device
    dev = libusb_open_device_with_vid_pid(NULL, VENDOR_LB, PRODUCT_MGPS);
    if (dev == NULL) {
        printf("lb_read: failed to find USB device\n");
        libusb_exit(NULL);
        return status;
    }
    
    // Get the device
    device = libusb_get_device(dev);
    
    // Check for kernel driver (Linux only)
    #ifdef __linux__
    if (libusb_kernel_driver_active(dev, INTERFACE_MGPS)) {
        ret = libusb_detach_kernel_driver(dev, INTERFACE_MGPS);
        if (ret != 0) {
            printf("lb_read: failed to detach kernel driver\n");
            libusb_close(dev);
            libusb_exit(NULL);
            return status;
        }
    }
    #endif
    
    // Get configuration descriptor
    ret = libusb_get_config_descriptor(device, CONFIGURATION_MGPS, &config);
    if (ret != 0) {
        printf("lb_read: failed to get configuration descriptor\n");
        libusb_close(dev);
        libusb_exit(NULL);
        return status;
    }
    
    // Claim interface
    ret = libusb_claim_interface(dev, INTERFACE_MGPS);
    if (ret != 0) {
        printf("lb_read: failed to claim interface\n");
        libusb_free_config_descriptor(config);
        libusb_close(dev);
        libusb_exit(NULL);
        return status;
    }
    
    // Set configuration if necessary
    int current_config;
    ret = libusb_get_configuration(dev, &current_config);
    if (ret != 0 || current_config != CONFIGURATION_MGPS + 1) {
        ret = libusb_set_configuration(dev, CONFIGURATION_MGPS + 1);
        if (ret != 0) {
            printf("lb_read: failed to set configuration\n");
            usb_safe_cleanup(dev, INTERFACE_MGPS);
            libusb_free_config_descriptor(config);
            libusb_exit(NULL);
            return status;
        }
    }
    
    // Packet parsing constants
    const int nhead = 4;
    const int offset1 = 10;
    const int offset2 = 46;
    unsigned char data[64];
    unsigned char packet[offset2 - offset1];
    bool packet_found = false;
    
    // Try to read data multiple times
    for (j = 0; j < ntry; j++) {
        int actual_length = 0;
        ret = libusb_interrupt_transfer(dev, 0x81, data, 64, &actual_length, timeout);
        
        if (ret != 0 || actual_length < nhead) {
            continue;
        }
        
        // Look for nav-pvt packet somewhere in the line
        for (i = 0; i < actual_length - nhead; i++) {
            // Skip the bytes for packet id, class id, length, and gps time of week of the nav epoch
            if (data[i] == 0xb5 && data[i+1] == 0x62 && data[i+2] == 0x01 && data[i+3] == 0x07) {
                // Check if nav-pvt packet appears too close to the end
                if (actual_length < i + offset2) {
                    break;
                }
                
                // Copy the bits we care about
                memcpy(packet, data + i + offset1, offset2 - offset1);
                packet_found = true;
                break;
            }
        }
        
        if (packet_found) {
            break;
        }
    }
    
    // Release USB device
    usb_safe_cleanup(dev, INTERFACE_MGPS);
    libusb_free_config_descriptor(config);
    
    // If no packet found, try to set the device and return
    if (!packet_found) {
        printf("lb_read: read failed\n");
        lb_set();
        libusb_exit(NULL);
        return status;
    }
    
    // Parse packet data
    uint16_t year;
    uint8_t month, day, hour, minute, second;
    int32_t nano_int, lon_int, lat_int, alt_int;
    
    // Extract time components
    memcpy(&year, packet + 0, 2);
    month = packet[2];
    day = packet[3];
    hour = packet[4];
    minute = packet[5];
    second = packet[6];
    
    // Check if datetime is valid
    if (year < 1970 || month < 1 || month > 12 || day < 1 || day > 31 ||
        hour > 23 || minute > 59 || second > 60) {
        printf("lb_read: bad datetime object\n");
        libusb_exit(NULL);
        return status;
    }
    
    // Extract validity flags and additional data
    uint8_t validity_flags = packet[7];
    snprintf(validity, 5, "%04x", validity_flags & 0x0F);
    
    memcpy(&nano_int, packet + 12, 4);
    *nano = nano_int * 1e-9;
    
    memcpy(&lon_int, packet + 20, 4);
    *lon = lon_int * 1e-7;
    
    memcpy(&lat_int, packet + 24, 4);
    *lat = lat_int * 1e-7;
    
    memcpy(&alt_int, packet + 32, 4);
    *alt = alt_int * 1e-3;
    
    // Set timestamp and time struct
    if (gpstime != NULL) {
        gpstime->tm_year = year - 1900;
        gpstime->tm_mon = month - 1;
        gpstime->tm_mday = day;
        gpstime->tm_hour = hour;
        gpstime->tm_min = minute;
        gpstime->tm_sec = second;
        gpstime->tm_isdst = -1;
    }
    
    // Calculate Unix timestamp
    struct tm epoch_tm = {0};
    epoch_tm.tm_year = 70;  // 1970
    epoch_tm.tm_mday = 1;   // 1st day
    
    struct tm time_tm = {0};
    time_tm.tm_year = year - 1900;
    time_tm.tm_mon = month - 1;
    time_tm.tm_mday = day;
    time_tm.tm_hour = hour;
    time_tm.tm_min = minute;
    time_tm.tm_sec = second;
    
    *tstamp = mktime(&time_tm);
    
    libusb_exit(NULL);
    status = true;
    return status;
}

// Set system clock from Leo Bodnar GPS time
bool set_clock_lb(int current_year) {
    bool status = false;
    time_t tstamp;
    double nano;
    char validity[5];
    double lon, lat, alt;
    struct tm gpstime;
    char cmd[100];
    
    // Set up the Leo Bodnar
    if (!lb_set()) {
        printf("unable to configure LB in set_clock_lb.\n");
        return status;
    }
    
    // Read the GPS time
    if (!lb_read(1000, 1000, &tstamp, &nano, validity, &lon, &lat, &alt, &gpstime)) {
        printf("unable to read time from LB in set_clock_lb.\n");
        return status;
    }
    
    // Verify the year is reasonable
    if (gpstime.tm_year + 1900 < current_year) {
        printf("GPS time is before %d and so is not to be believed. Ignoring.\n", current_year);
        return status;
    } else {
        char timestr[100];
        strftime(timestr, sizeof(timestr), "%c", &gpstime);
        printf("GPS time of %s seems OK. continuing.\n", timestr);
    }
    
    // Set the system time
    snprintf(cmd, sizeof(cmd), "sudo date -s \"%02d/%02d/%04d %02d:%02d:%02d\"", 
             gpstime.tm_mon + 1, gpstime.tm_mday, gpstime.tm_year + 1900, 
             gpstime.tm_hour, gpstime.tm_min, gpstime.tm_sec);
    
    if (system(cmd) != 0) {
        printf("Failed to set system time.\n");
        return status;
    }
    
    status = true;
    return status;
}
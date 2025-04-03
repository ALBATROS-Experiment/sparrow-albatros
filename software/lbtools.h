#ifndef LBTOOLS_H
#define LBTOOLS_H

#include <stdbool.h>
#include <time.h>

/**
 * Set Leo Bodnar into a mode where it reports nav-data packets.
 * 
 * @return True for success, False for error.
 */
bool lb_set(void);

/**
 * Read GPS time stamp from Leo Bodnar.
 *
 * @param ntry Maximum number of read attempts to find nav-data (default 1000)
 * @param timeout USB read timeout in milliseconds (default 1000)
 * @param tstamp Pointer to store Unix timestamp
 * @param nano Pointer to store nanoseconds precision
 * @param validity Pointer to store validity flag string (must be at least 5 bytes)
 * @param lon Pointer to store longitude
 * @param lat Pointer to store latitude
 * @param alt Pointer to store altitude
 * @param gpstime Pointer to store time struct
 * @return True for success, False for error
 */
bool lb_read(int ntry, int timeout, time_t *tstamp, double *nano, char *validity, 
             double *lon, double *lat, double *alt, struct tm *gpstime);

/**
 * Used in the ALBATROS config script.
 * Initiates the LB with the lb_set() command and then sets system time to the LB GPS time.
 *
 * @param current_year Minimum valid year to accept from GPS (as sanity check)
 * @return True for success, False for error
 */
bool set_clock_lb(int current_year);

#endif /* LBTOOLS_H */
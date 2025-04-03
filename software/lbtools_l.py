import datetime
import usb.core                 # https://github.com/pyusb/pyusb
import struct
import os


def usb_safe_cleanup(dev,interface):
    try:
        usb.util.release_interface(dev,interface)
        usb.util.dispose_resources(dev)
    except Exception as e:
        print(e,' failure in usb_safe_cleanup')
        return False
    return True



#====================================================================
def lb_set():
    """
    Set Leo Bodnar into a mode where it reports nav-data packets.
    Returns True for success, False for error.
    """

    status = False
    VENDOR_LB = 0x1DD2     # Leo Bodnar's Vendor ID
    PRODUCT_MGPS = 0x2211  # Mini GPS product ID
    CONFIGURATION_MGPS = 0 # 1-based
    INTERFACE_MGPS = 0     # 0-based
    SETTING_MGPS = 0       # 0-based
    ENDPOINT_MGPS = 0      # 0-based


    # Magic command to set the LB, courtesy of Simon
    buffer = [8, 6, 1, 8, 0, 0x01, 0x07, 10]

    dev = usb.core.find(idVendor=VENDOR_LB, idProduct=PRODUCT_MGPS)

    if dev is None:
        print("lb_set: failed to find USB device")
        return status

    desconfig = dev[0] #desired config

    try:
        dev.reset()
    except:
        print("lb_set: failed to reset device")
        return status

    #linux only command to detach kernal:
    try:
    	if dev.is_kernel_driver_active(INTERFACE_MGPS):
    		dev.detach_kernel_driver(INTERFACE_MGPS)
    except:
      	print("lb_set: failed to detach kernel driver")
      	return status
    try:
        configuration = dev.get_active_configuration()
    except:
        print("lb_set: failed to get configuration")
        return status

    interface = configuration[(INTERFACE_MGPS, SETTING_MGPS)]
    endpoint = interface[ENDPOINT_MGPS]

    try:
        usb.util.claim_interface(dev, interface)
    except:
        print("lb_set: failed to claim interface")
        return status

    if configuration.bConfigurationValue != desconfig.bConfigurationValue:
        try:
            dev.set_configuration(desconfig)
        except:
            print("lb_set: failed to set configuration")
            #usb.util.release_interface(dev, interface)
            #usb.util.dispose_resources(dev)
            usb_safe_cleanup(dev,interface)
            return status

    try:
        ret = dev.ctrl_transfer(0x21, 9, 0x0300, 0, buffer)   # ret should be 8
        usb.util.release_interface(dev, interface)
        usb.util.dispose_resources(dev)
    except:
        print("lb_set: failed to write to device")
        #usb.util.release_interface(dev, interface)
        #usb.util.dispose_resources(dev)
        usb_safe_cleanup(dev,interface)
        return status

    status = True
    return status

#====================================================================
def lb_read(ntry=1000, timeout=1000):
    """
    Read GPS time stamp from Leo Bodnar.

    ntry: maximum number of read attempts to find nav-data
    timeout: USB read timeout in milliseconds

    Returns Linux timestamp, (precision, validity, lon, lat, alt), and datetime object tuple
    """

    tstamp = None
    auxdat = None
    gpstime = None

    VENDOR_LB = 0x1DD2     # Leo Bodnar's Vendor ID
    PRODUCT_MGPS = 0x2211  # Mini GPS product ID
    CONFIGURATION_MGPS = 0 # 1-based
    INTERFACE_MGPS = 0     # 0-based
    SETTING_MGPS = 0       # 0-based
    ENDPOINT_MGPS = 0      # 0-based

    dev = usb.core.find(idVendor=VENDOR_LB, idProduct=PRODUCT_MGPS)

    if dev is None:
        print("lb_read: failed to find USB device")
        return tstamp, auxdat, gpstime

    desconfig = dev[0] #desired config

    #linux only command to detach kernal:
    try:
    	if dev.is_kernel_driver_active(INTERFACE_MGPS):
      		dev.detach_kernel_driver(INTERFACE_MGPS)
    except:
      	print("lb_read: failed to detach kernel driver")
      	return tstamp, auxdat, gpstime
    try:
        configuration = dev.get_active_configuration()
    except:
        print("lb_read: failed to get configuration")
        return tstamp, auxdat, gpstime

    interface = configuration[(INTERFACE_MGPS, SETTING_MGPS)]
    endpoint = interface[ENDPOINT_MGPS]

    try:
        usb.util.claim_interface(dev, interface)
    except:
        print("lb_read: failed to claim interface")
        return tstamp, auxdat, gpstime

    if configuration.bConfigurationValue != desconfig.bConfigurationValue:
        try:
            dev.set_configuration(desconfig)
        except:
            print("lb_read: failed to set configuration")
            #usb.util.release_interface(dev, interface)
            #usb.util.dispose_resources(dev)
            usb_safe_cleanup(dev,interface)
            return tstamp, auxdat, gpstime

    packet = None
    nhead = 4
    offset1 = 10
    offset2 = 46

    for j in range(ntry):
        try:
            data = dev.read(0x81, 64, timeout=timeout)
            usb.util.release_interface(dev, interface)
            usb.util.dispose_resources(dev)
        except Exception as e:
            print("lb_read: read error")
            print(e)
            #usb.util.release_interface(dev, interface)
            #usb.util.dispose_resources(dev)
            usb_safe_cleanup(dev,interface)
            lb_set()
            return tstamp, auxdat, gpstime

        if len(data) < nhead:
            continue
        # Look for nav-pvt packet somewhere in the line
        for i in range(len(data)-nhead):
            # Look for nav-pvt packet somewhere in the line
            # Skip the bytes for packet id, class id, length, and gps time of week of the nav epoch
             if data[i:i+nhead].tolist() == [0xb5, 0x62, 0x01, 0x07]:
                # Check if nav-pvt packet appears too close to the end
                if len(data) < i+offset2:
                    break
                # ...otherwise snarf the bits we care about
                packet = data[i+offset1:i+offset2]
                break
        if packet:
            break
    if packet is None:
        print("lb_read: read failed")
        #usb.util.release_interface(dev, interface)
        #usb.util.dispose_resources(dev)
        usb_safe_cleanup(dev,interface)
        lb_set()
        return tstamp, auxdat, gpstime

    try:
        year = struct.unpack('<H', packet[0:2])
        year = year[0]

        month = struct.unpack('<B', packet[2:3])
        month = month[0]

        day = struct.unpack('<B', packet[3:4])
        day = day[0]

        hour = struct.unpack('<B', packet[4:5])
        hour = hour[0]

        minute = struct.unpack('<B', packet[5:6])
        minute = minute[0]

        second = struct.unpack('<B', packet[6:7])
        second = second[0]
    except:
        print("lb_read(): bad tstamp unpack")
        return tstamp, auxdat, gpstime

    try:
        datetime.datetime(year, month, day, hour, minute, second)
    except:
        print("lb_read: bad datetime object")
        return tstamp, auxdat, gpstime

    try:
        validity = packet[7]
        validity = "{0:b}".format(validity)  # format as binary string to get the bitfield
        validity = (4-len(validity))*'0'+validity # use the 4 bits of validity to check for a good reading

        nano = struct.unpack('<l', packet[12:16])
        nano = nano[0]*10**-9

        lon = struct.unpack('<l', packet[20:24])
        lon = lon[0]*10**-7

        lat = struct.unpack('<l', packet[24:28])
        lat = lat[0]*10**-7

        alt = struct.unpack('<l', packet[32:36])
        alt = alt[0]*10**-3
    except:
        print("lb_read: bad auxdat unpack")
        return tstamp, auxdat, gpstime

    tstamp = (datetime.datetime(year,month,day,hour,minute,second)-datetime.datetime(1970,1,1)).total_seconds()
    auxdat = (nano, validity, lon, lat, alt)
    gpstime = datetime.datetime(year, month, day, hour, minute, second)

    return tstamp, auxdat, gpstime

#====================================================================
def set_clock_lb(current_year=2025):
    """
    Used in the ALBATROS config script.
    Initiates the LB with the lb_set() command and then sets system time to the LB GPS time.

    """
    lbset = lb_set()
    if lbset is False:
        print("unable to configure LB in set_clock_lb.")
        return False
    gpsread = lb_read()
    mytime = gpsread[2]
    if mytime is None:
        print("unable to read time from LB in set_clock_lb.")
        return False
    myyear=int(mytime.ctime()[-4:])
    if (myyear<current_year):
        print('GPS time is before '+repr(current_year)+' and so is not to be believed.  Ignoring.')
        return False
    else:
        print('GPS time of ',mytime.ctime(),' seems OK.  continuing.')
    to_exec='sudo date -s " %s "' % mytime.ctime()
    os.system(to_exec)
    return True

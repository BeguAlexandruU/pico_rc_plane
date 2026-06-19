from machine import UART, Pin

# global variables
gps = None
lat = 0.0
lon = 0.0
gps_buffer = ""

def setup():
    global gps
    gps = UART(0, baudrate=9600, tx=Pin(12), rx=Pin(13), timeout=0)
    print("GPS Inițializat în mod Non-Blocant")

def update():
    global gps, lat, lon, gps_buffer
    
    # read full buffer from UART
    if gps.any():
        try:
            raw_data = gps.read(gps.any())
            if raw_data:
                gps_buffer += raw_data.decode('utf-8', 'ignore')
        except Exception as e:
            print(f"[Eroare Citire UART]: {e}")
            return

    # Process only the one complete line in the buffer
    if "\n" in gps_buffer:

        line, gps_buffer = gps_buffer.split("\n", 1)
        line = line.strip()
        # print(f"GPS: {line}")
        
        # if the line is not a GPRMC sentence, ignore it
        if not line.startswith('$GPRMC'):
            return
            
        # Parse the GPRMC sentence
        try:
            p = line.split(',')
            if len(p) > 6 and p[2] == 'A' and p[3] != '' and p[5] != '':
                
                # convert DDMM.MMMMM to Decimal Degrees
                lat_deg = float(p[3][:2])
                lat_min = float(p[3][2:])
                lat = lat_deg + (lat_min / 60.0)
                
                lon_deg = float(p[5][:3])
                lon_min = float(p[5][3:])
                lon = lon_deg + (lon_min / 60.0)
                
                if p[4] == 'S': lat = -lat
                if p[6] == 'W': lon = -lon
                
                #print(f"GPS: {lat:.6f}, {lon:.6f}")
                
        except Exception as e:
            print(f"[Eroare Parsare]: {e}")

from machine import UART, Pin

gps = None
lat = 0
lon = 0

def setup():
    global gps
    gps = UART(0, baudrate=9600, tx=Pin(12), rx=Pin(13))

def update():
    global buffer, gps, lat, lon
    if gps.any():
        try:
            line = gps.readline().decode('utf-8')
            
            if line.startswith('$GPRMC'):
                p = line.split(',')
                
                # p[2] == 'A' (Active)
                if len(p) > 6 and p[2] == 'A':
                    
                    # Conversie rapidă inline din DDMM.MMMMM în Grade Zecimale
                    lat = float(p[3][:2]) + float(p[3][2:]) / 60.0
                    lon = float(p[5][:3]) + float(p[5][3:]) / 60.0
                    
                    # Corecție pentru emisferele Sud/Vest
                    if p[4] == 'S': lat = -lat
                    if p[6] == 'W': lon = -lon
                    
                    # Afișare
                    # print(f"GPS: {lat:.6f}, {lon:.6f} -> https://maps.google.com/?q={lat:.6f},{lon:.6f}")
                    
        except:
            pass
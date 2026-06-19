from machine import UART, Pin

# Variabile globale
gps = None
lat = 0.0
lon = 0.0
gps_buffer = "" # Buffer local pentru acumularea caracterelor

def setup():
    global gps
    # CRUCIAL: Setează timeout = 0. 
    # Asta înseamnă că UART nu va aștepta niciodată dacă nu sunt date, ci va returna instant.
    gps = UART(0, baudrate=9600, tx=Pin(12), rx=Pin(13), timeout=0)
    print("GPS Inițializat în mod Non-Blocant")

def update():
    global gps, lat, lon, gps_buffer
    
    # 1. Citim TOATE caracterele care se află DEJA în bufferul hardware în acest moment.
    # Fiind timeout=0, operația durează sub o microsecundă.
    if gps.any():
        try:
            raw_data = gps.read(gps.any())
            if raw_data:
                # Adăugăm datele noi în bufferul nostru textil
                gps_buffer += raw_data.decode('utf-8', 'ignore')
        except Exception as e:
            print(f"[Eroare Citire UART]: {e}")
            return

    # 2. PROCESĂM MAXIM O SINGURĂ LINIE PER CICLU (Time-Slicing)
    # În loc de 'while', folosim 'if' pentru a lăsa bucla principală să respire.
    if "\n" in gps_buffer:
        # Preluăm doar prima linie completă și lăsăm restul în buffer pentru ciclurile următoare
        line, gps_buffer = gps_buffer.split("\n", 1)
        line = line.strip()
        # print(f"GPS: {line}")
        
        # Dacă linia nu este cea care ne interesează, ieșim rapid din funcție
        if not line.startswith('$GPRMC'):
            return
            
        # Parsarea propriu-zisă (se execută doar o dată pe secundă pentru linia corectă)
        try:
            p = line.split(',')
            if len(p) > 6 and p[2] == 'A' and p[3] != '' and p[5] != '':
                
                # Conversie DDMM.MMMMM în Grade Zecimale
                lat_deg = float(p[3][:2])
                lat_min = float(p[3][2:])
                lat = lat_deg + (lat_min / 60.0)
                
                lon_deg = float(p[5][:3])
                lon_min = float(p[5][3:])
                lon = lon_deg + (lon_min / 60.0)
                
                if p[4] == 'S': lat = -lat
                if p[6] == 'W': lon = -lon
                
                # Opțional: poți scoate print-urile de tot dacă vrei performanță maximă
                #print(f"GPS: {lat:.6f}, {lon:.6f}")
                
        except Exception as e:
            print(f"[Eroare Parsare]: {e}")

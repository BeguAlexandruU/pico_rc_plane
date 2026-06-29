

import argparse
import math
import sys
import time

try:
    import serial  
except ImportError:
    sys.exit("Lipseste pyserial. Instaleaza cu:  pip install pyserial")


BASE_LAT = 47.150476
BASE_LON = 27.636506

M_PER_DEG_LAT = 111_320.0
M_PER_DEG_LON = 111_320.0 * math.cos(math.radians(BASE_LAT))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generator de telemetrie sintetica (GCS).")
    p.add_argument("port", nargs="?", default="COM10",
                   help="port serial (implicit COM10)")
    p.add_argument("--baud", type=int, default=115200, help="viteza serial (implicit 115200)")
    p.add_argument("--rate", type=float, default=50.0, help="frecventa de emisie Hz (implicit 50)")
    p.add_argument("--duration", type=float, default=0.0,
                   help="durata in secunde; 0 = nelimitat (implicit 0)")
    return p.parse_args()


def flight_state(t: float) -> dict:
    """
    Returneaza starea simulata a aeronavei la momentul t (secunde de la start).

    Profilul are trei faze: urcare (0-15 s), croaziera cu viraje (15-... s),
    suprapuse cu oscilatii fine pentru un aspect natural al datelor.
    """
    # --- Altitudine: urcare lina la ~60 m, apoi mici variatii ---
    climb = 60.0 * (1.0 - math.exp(-t / 8.0))
    altitude = climb + 3.0 * math.sin(t * 0.25)

    # --- Directie (heading): viraje lente, un circuit complet la ~80 s ---
    turn_rate = 4.5  # grade/s in viraj
    heading = (turn_rate * t) % 360.0

    # --- Ruliu: corelat cu virajul (bancare in directia virajului) ---
    # in croaziera, alterneaza intre +/- ~20 grade
    roll = 20.0 * math.sin(t * 0.20) + 2.0 * math.sin(t * 1.7)

    # --- Tangaj: usor pozitiv la urcare, apoi mic in jurul lui 0 ---
    pitch_climb = 8.0 * math.exp(-t / 8.0)
    pitch = pitch_climb + 4.0 * math.sin(t * 0.35)

    # --- Pozitie GPS: deplasare de-a lungul directiei curente ---
    # viteza la sol ~12 m/s; integram pe un pas mic folosind t direct
    speed = 12.0  # m/s
    # raza circuitului decurge din viteza si turn_rate
    omega = math.radians(turn_rate)  # rad/s
    radius = speed / omega if omega > 1e-6 else 0.0
    # pozitie pe cerc (centru deplasat ca sa porneasca din BASE)
    ang = math.radians(heading)
    dx = radius * math.sin(ang)              # est (m)
    dy = radius * (1.0 - math.cos(ang))      # nord (m)
    lat = BASE_LAT + dy / M_PER_DEG_LAT
    lon = BASE_LON + dx / M_PER_DEG_LON

    return {
        "roll": roll, "pitch": pitch, "heading": heading,
        "altitude": altitude, "lat": lat, "lon": lon,
    }


def main() -> None:
    args = parse_args()
    period = 1.0 / args.rate if args.rate > 0 else 0.02

    try:
        ser = serial.Serial(args.port, args.baud)
    except serial.SerialException as e:
        sys.exit(f"Nu pot deschide portul {args.port}: {e}")

    print(f"Emit telemetrie sintetica pe {args.port} @ {args.baud} baud, "
          f"{args.rate:.0f} Hz. Ctrl+C pentru oprire.")

    start = time.perf_counter()
    next_tick = start
    try:
        while True:
            now = time.perf_counter()
            t = now - start
            if args.duration > 0 and t >= args.duration:
                break

            s = flight_state(t)
            ts_ms = int(t * 1000)
            line = (f"{s['roll']:.4f},{s['pitch']:.4f},{s['heading']:.4f},"
                    f"{s['altitude']:.4f},{s['lat']:.6f},{s['lon']:.6f},{ts_ms}\n")
            ser.write(line.encode("utf-8"))

            # temporizare stabila la frecventa ceruta
            next_tick += period
            sleep = next_tick - time.perf_counter()
            if sleep > 0:
                time.sleep(sleep)
            else:
                next_tick = time.perf_counter()
    except KeyboardInterrupt:
        print("\nOprit.")
    finally:
        ser.close()


if __name__ == "__main__":
    main()

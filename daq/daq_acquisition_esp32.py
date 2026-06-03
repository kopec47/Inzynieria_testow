import threading
import time


class ESP32JoystickAcquisition:
    """Continuous acquisition from ESP32 joystick logger over USB Serial."""

    def __init__(self, port="COM7", baud_rate=115200, voltage_min=0.0, voltage_max=3.3):
        self.port = port
        self.baud_rate = baud_rate
        self.voltage_min = voltage_min
        self.voltage_max = voltage_max
        self.buffer = []
        self.lock = threading.Lock()
        self.command_lock = threading.Lock()
        self.is_running = False
        self.thread = None
        self._serial = None
        self._first_time_ms = None
        self.frequency = 10

    def configure(self, frequency=None, voltage_min=None, voltage_max=None):
        if frequency is not None:
            self.frequency = max(1, int(float(frequency)))
        if voltage_min is not None:
            self.voltage_min = float(voltage_min)
        if voltage_max is not None:
            self.voltage_max = float(voltage_max)
        if self.voltage_min >= self.voltage_max:
            raise ValueError("Minimalny zakres AI musi byc mniejszy od maksymalnego.")

    def start(self):
        if self.is_running:
            return
        try:
            import serial
        except ImportError as exc:
            raise RuntimeError("Brak biblioteki pyserial. Zainstaluj pakiet: pip install pyserial") from exc

        try:
            self._serial = serial.Serial(self.port, self.baud_rate, timeout=0.2)
        except Exception as exc:
            raise RuntimeError(f"Nie mozna otworzyc portu ESP32 {self.port}: {exc}") from exc

        self._first_time_ms = None
        self.is_running = True
        self.send_command(f"RATE,{self.frequency}")
        self.thread = threading.Thread(target=self._acquisition_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None
        if self._serial is not None:
            try:
                self._serial.close()
            finally:
                self._serial = None

    def get_samples(self):
        with self.lock:
            samples = list(self.buffer)
            self.buffer.clear()
        return samples

    def send_command(self, command):
        if self._serial is None or not self._serial.is_open:
            raise RuntimeError("Port ESP32 nie jest otwarty. Uruchom najpierw akwizycje.")
        data = f"{command.strip()}\n".encode("utf-8")
        with self.command_lock:
            self._serial.write(data)
            self._serial.flush()

    def _acquisition_loop(self):
        while self.is_running and self._serial is not None:
            try:
                raw_line = self._serial.readline()
            except Exception:
                if self.is_running:
                    time.sleep(0.1)
                continue

            if not raw_line:
                continue

            try:
                line = raw_line.decode("utf-8", errors="replace").strip()
                sample = self._parse_line(line)
            except ValueError:
                continue

            with self.lock:
                self.buffer.append(sample)

    def _parse_line(self, line):
        if not line or line.startswith("#") or line.lower().startswith("time_ms"):
            raise ValueError("Linia informacyjna ESP32.")

        parts = [part.strip() for part in line.split(",")]
        if len(parts) != 5:
            raise ValueError("Niepoprawny format CSV z ESP32.")

        time_ms = int(parts[0])
        ai0_v = float(parts[1])
        ai1_v = float(parts[2])
        di0 = int(parts[3])
        di1 = int(parts[4])

        if self._first_time_ms is None:
            self._first_time_ms = time_ms
        elapsed_time_ms = time_ms - self._first_time_ms

        span = self.voltage_max - self.voltage_min
        potentiometer = (ai0_v - self.voltage_min) / span if span else 0.0
        potentiometer = max(0.0, min(1.0, potentiometer))

        return {
            "time_s": elapsed_time_ms / 1000.0,
            "ai_v": ai0_v,
            "ai1_v": ai1_v,
            "di": int(bool(di0 or di1)),
            "di0": di0,
            "di1": di1,
            "potentiometer": potentiometer,
            "proximity": di0,
            "switch": di1,
        }

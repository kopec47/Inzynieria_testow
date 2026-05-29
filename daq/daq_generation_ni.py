import math
import threading
import time


class NIDaqGeneration:
    """Analog output generation using NI-DAQmx."""

    def __init__(self, device_name="Dev1", ao_channel="ao0"):
        self.device_name = device_name
        self.ao_channel = ao_channel
        self.is_running = False
        self.thread = None
        self.shape = "sinusoida"
        self.amplitude = 5.0
        self.frequency = 1.0
        self.duty_cycle = 50.0
        self.current_value = 0.0
        self.lock = threading.Lock()
        self._start_time = None
        self._task = None

    def set_sine(self, amplitude, frequency):
        with self.lock:
            self.shape = "sinusoida"
            self.amplitude = float(amplitude)
            self.frequency = max(0.01, float(frequency))

    def set_sin(self, amplitude, frequency):
        self.set_sine(amplitude, frequency)

    def set_pwm(self, amplitude, duty_cycle, frequency=1.0):
        with self.lock:
            self.shape = "PWM"
            self.amplitude = float(amplitude)
            self.frequency = max(0.01, float(frequency))
            self.duty_cycle = max(0.0, min(100.0, float(duty_cycle)))

    def start(self):
        if self.is_running:
            return
        try:
            import nidaqmx
        except ImportError as exc:
            raise RuntimeError("Brak biblioteki nidaqmx. Zainstaluj sterownik NI-DAQmx oraz pakiet Python nidaqmx.") from exc

        self._task = nidaqmx.Task()
        self._task.ao_channels.add_ao_voltage_chan(self._full_channel(self.ao_channel))
        self.is_running = True
        self._start_time = time.monotonic()
        self.thread = threading.Thread(target=self._generation_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.is_running = False
        if self.thread is not None:
            self.thread.join(timeout=1.0)
            self.thread = None
        if self._task is not None:
            try:
                self._task.write(0.0, auto_start=True)
            finally:
                self._task.close()
                self._task = None
        with self.lock:
            self.current_value = 0.0
            self._start_time = None

    def get_value(self):
        with self.lock:
            return self.current_value

    def get_elapsed_time(self):
        with self.lock:
            start_time = self._start_time
        if start_time is None:
            return 0.0
        return time.monotonic() - start_time

    def _generation_loop(self):
        while self.is_running:
            t = self.get_elapsed_time()
            with self.lock:
                shape = self.shape
                amplitude = self.amplitude
                frequency = self.frequency
                duty_cycle = self.duty_cycle

            if shape == "sinusoida":
                value = amplitude * math.sin(2 * math.pi * frequency * t)
            else:
                period = 1.0 / frequency
                value = amplitude if (t % period) < period * duty_cycle / 100.0 else 0.0

            with self.lock:
                self.current_value = value
            self._task.write(value, auto_start=True)
            time.sleep(0.01)

    def _full_channel(self, channel):
        channel = channel.strip()
        if "/" in channel:
            return channel
        return f"{self.device_name}/{channel}"

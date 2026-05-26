import math
import threading
import time


class AnalogGeneration:
    """Continuous simulated analog output generation."""

    def __init__(self, channel="AO0"):
        self.channel = channel
        self.is_running = False
        self.thread = None
        self.shape = "sinusoida"
        self.amplitude = 5.0
        self.frequency = 1.0
        self.duty_cycle = 50.0
        self.current_value = 0.0
        self.lock = threading.Lock()

    def set_sine(self, amplitude, frequency):
        self.shape = "sinusoida"
        self.amplitude = float(amplitude)
        self.frequency = max(0.01, float(frequency))

    def set_sin(self, amplitude, frequency):
        self.set_sine(amplitude, frequency)

    def set_pwm(self, amplitude, duty_cycle, frequency=1.0):
        self.shape = "PWM"
        self.amplitude = float(amplitude)
        self.frequency = max(0.01, float(frequency))
        self.duty_cycle = max(0.0, min(100.0, float(duty_cycle)))

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._generation_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.is_running = False
        if self.thread is not None:
            self.thread.join(timeout=1.0)
            self.thread = None

    def get_value(self):
        with self.lock:
            return self.current_value

    def _generation_loop(self):
        start_time = time.monotonic()
        while self.is_running:
            t = time.monotonic() - start_time
            if self.shape == "sinusoida":
                value = self.amplitude * math.sin(2 * math.pi * self.frequency * t)
            else:
                period = 1.0 / self.frequency
                value = self.amplitude if (t % period) < period * self.duty_cycle / 100.0 else 0.0

            with self.lock:
                self.current_value = value
            time.sleep(0.01)

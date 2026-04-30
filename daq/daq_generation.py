import threading
import time
import math

class AnalogGeneration:
    def __init__(self):
        self.is_running = False
        self.thread = None
        self.shape = "sinusoida"
        self.amplitude = 5.0
        self.frequency = 1.0
        self.duty_cycle = 50.0

    def set_sine(self, amp, freq):
        self.shape = "sinusoida"; self.amplitude = amp; self.frequency = freq

    def set_pwm(self, amp, dc, freq=1.0):
        self.shape = "PWM"; self.amplitude = amp; self.duty_cycle = dc; self.frequency = freq

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._generation_loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.is_running = False

    def _generation_loop(self):
        t0 = time.time()
        while self.is_running:
            t = time.time() - t0
            if self.shape == "sinusoida":
                _ = self.amplitude * math.sin(2 * math.pi * self.frequency * t)
            elif self.shape == "PWM":
                period = 1.0 / self.frequency
                _ = self.amplitude if (t % period) < (period * self.duty_cycle / 100.0) else 0
            time.sleep(0.01)
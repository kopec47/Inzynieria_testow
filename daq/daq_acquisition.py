import math
import random
import threading
import time


class AnalogAcquisition:
    """Continuous simulated acquisition of analog and digital input samples."""

    def __init__(self, frequency=100, voltage_min=-10.0, voltage_max=10.0):
        self.frequency = frequency
        self.voltage_min = voltage_min
        self.voltage_max = voltage_max
        self.buffer = []
        self.lock = threading.Lock()
        self.is_running = False
        self.thread = None
        self._sample_index = 0
        self._start_time = None

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
        self.is_running = True
        self._sample_index = 0
        self._start_time = time.monotonic()
        self.thread = threading.Thread(target=self._acquisition_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None

    def _acquisition_loop(self):
        while self.is_running:
            loop_start = time.monotonic()
            samples_per_tick = max(1, round(self.frequency * 0.1))
            tick_samples = [self._build_sample() for _ in range(samples_per_tick)]
            with self.lock:
                self.buffer.extend(tick_samples)

            elapsed = time.monotonic() - loop_start
            time.sleep(max(0.0, 0.1 - elapsed))

    def _build_sample(self):
        timestamp = self._sample_index / self.frequency
        span = self.voltage_max - self.voltage_min
        center = self.voltage_min + span / 2.0
        amplitude = span * 0.45
        analog = center + amplitude * math.sin(2 * math.pi * 0.5 * timestamp)
        analog += random.uniform(-0.03 * span, 0.03 * span)
        analog = max(self.voltage_min, min(self.voltage_max, analog))

        proximity = analog > center
        switch = (self._sample_index // max(1, self.frequency)) % 2 == 1
        digital = int(proximity or switch)
        potentiometer = (analog - self.voltage_min) / span

        sample = {
            "time_s": timestamp,
            "ai_v": analog,
            "di": digital,
            "potentiometer": potentiometer,
            "proximity": int(proximity),
            "switch": int(switch),
        }
        self._sample_index += 1
        return sample

    def get_samples(self):
        with self.lock:
            samples = list(self.buffer)
            self.buffer.clear()
        return samples

import threading
import time
import math
import random

class AnalogAcquisition:
    def __init__(self, frequency=100):
        self.frequency = frequency
        self.buffer = []
        self.lock = threading.Lock()
        self.is_running = False
        self.thread = None

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._acquisition_loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join()

    def _acquisition_loop(self):
        while self.is_running:
            loop_start = time.time()
            # Symulacja danych (sinusoida + szum)
            val = math.sin(time.time() * 2) * 5 + random.uniform(-0.2, 0.2)
            with self.lock:
                self.buffer.append(val)
            
            # Pętla co ok 100ms
            time.sleep(0.1)

    def get_samples(self):
        with self.lock:
            samples = list(self.buffer)
            self.buffer.clear()
        return samples
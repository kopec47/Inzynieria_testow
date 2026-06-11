import math
import threading
import time


class AnalogGeneration:

    def __init__(self, channel="AO0"):
        # Parametry i stan symulowanego wyjscia analogowego.
        self.channel = channel
        self.is_running = False
        self.thread = None
        self.shape = "sinusoida"
        self.amplitude = 5.0
        self.frequency = 1.0
        self.duty_cycle = 50.0
        self.current_value = 0.0
        self.lock = threading.Lock()
        self._start_time = None

    def set_sine(self, amplitude, frequency):
        # Ustawia parametry sygnalu sinusoidalnego.
        with self.lock:
            self.shape = "sinusoida"
            self.amplitude = float(amplitude)
            self.frequency = max(0.01, float(frequency))

    def set_sin(self, amplitude, frequency):
        # Alias zostawiony dla zgodnosci nazewnictwa.
        self.set_sine(amplitude, frequency)

    def set_pwm(self, amplitude, duty_cycle, frequency=1.0):
        # Ustawia parametry sygnalu PWM.
        with self.lock:
            self.shape = "PWM"
            self.amplitude = float(amplitude)
            self.frequency = max(0.01, float(frequency))
            self.duty_cycle = max(0.0, min(100.0, float(duty_cycle)))

    def start(self):
        # Uruchamia generacje w osobnym watku.
        if self.is_running:
            return
        self.is_running = True
        self._start_time = time.monotonic()
        self.thread = threading.Thread(target=self._generation_loop, daemon=True)
        self.thread.start()

    def stop(self):
        # Zatrzymuje generacje i zeruje aktualna wartosc.
        self.is_running = False
        if self.thread is not None:
            self.thread.join(timeout=1.0)
            self.thread = None
        with self.lock:
            self.current_value = 0.0
            self._start_time = None

    def get_value(self):
        # Zwraca aktualnie wygenerowana wartosc sygnalu.
        with self.lock:
            return self.current_value

    def get_elapsed_time(self):
        # Zwraca czas od startu generacji.
        with self.lock:
            start_time = self._start_time
        if start_time is None:
            return 0.0
        return time.monotonic() - start_time

    def _generation_loop(self):
        # W tle obliczamy kolejne wartosci sinusoidy albo PWM.
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
            time.sleep(0.01)

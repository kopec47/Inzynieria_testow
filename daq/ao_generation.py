import threading 
import time
import math

class AnalogGeneration:
    def __init__(self, channel = "AO0"):
        self.channel = channel
        self.is_running = False
        self.thread = None


        self.shape = "sinusoida"
        self.amplitude = 5.0
        self.frequency = 1.0
        self.duty_cycle = 50.0

    def set_sin(self, amplitude, frequency):
        self.shape = "sinusoida"
        self.amplitude = amplitude
        self.frequency = frequency

    def set_pwm(self, amplitude, duty_cycle, frequency = 1.0):
        self.shape = "pwm"
        self.amplitude = amplitude
        self.frequency = frequency
        self.duty_cycle = duty_cycle

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._generation_loop, daemon=True)

            self.thread.start()
            print(f"[{self.channel}] generacja sygnalu ({self.shape}) rozpoczęta.")

    def stop(self):
        self.is_running = False
        if self.thread is not None:
            self.thread.join()
            print(f"[{self.channel}] generacja sygnalu ({self.shape}) zatrzymana.") 
    
    def _generation_loop(self):
        """petla dzialajaca w tle, ktora na biezaco wylicza wartosc sygnalu"""
        start_time = time.time()    

        while self.is_running:
            current_time = time.time() - start_time
            output_value = 0.0

            if self.shape == "sinusoida":
                output_value = self.amplitude * math.sin(2 * math.pi * self.frequency * current_time)
            elif self.shape == "pwm":
                period = 1.0 / self.frequency if self.frequency > 0 else 1.0
                time_in_period = current_time % period
                high_time = period * (self.duty_cycle / 100.0)

                if time_in_period < high_time:
                    output_value = self.amplitude
                else:
                    output_value = 0.0

            time.sleep(0.01)  # symulacja czasu potrzebnego na wygenerowanie sygnalu


if __name__ == "__main__":
    ao = AnalogGeneration()

    ao.set_sin(amplitude=10, frequency=2)
    ao.start()
    time.sleep(2)
    ao.stop()

    print("-" * 30)

    ao.set_pwm(amplitude=5, duty_cycle=25)
    ao.start()
    time.sleep(2)

    ao.stop()
    
# Import klasy odpowiedzialnej za generowanie sygnalu AO.
from daq_generation import AnalogGeneration


# Ten kod wykona sie tylko przy bezposrednim uruchomieniu tego pliku.
if __name__ == "__main__":
    import time

    # Tworzymy obiekt generatora analogowego.
    ao = AnalogGeneration()

    # Test generacji sinusoidy przez 2 sekundy.
    ao.set_sine(amplitude=10, frequency=2)
    ao.start()
    time.sleep(2)
    ao.stop()

    # Test generacji sygnalu PWM przez 2 sekundy.
    ao.set_pwm(amplitude=5, duty_cycle=25, frequency=1)
    ao.start()
    time.sleep(2)
    ao.stop()

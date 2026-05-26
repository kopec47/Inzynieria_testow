from daq_generation import AnalogGeneration


if __name__ == "__main__":
    import time

    ao = AnalogGeneration()
    ao.set_sine(amplitude=10, frequency=2)
    ao.start()
    time.sleep(2)
    ao.stop()

    ao.set_pwm(amplitude=5, duty_cycle=25, frequency=1)
    ao.start()
    time.sleep(2)
    ao.stop()

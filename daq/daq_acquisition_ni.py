import threading
import time


class NIDaqAcquisition:
    """Continuous analog/digital acquisition using NI-DAQmx."""

    def __init__(self, device_name="Dev1", ai_channel="ai0", di_line="port0/line0", frequency=100,
                 voltage_min=-10.0, voltage_max=10.0):
        self.device_name = device_name
        self.ai_channel = ai_channel
        self.di_line = di_line
        self.frequency = frequency
        self.voltage_min = voltage_min
        self.voltage_max = voltage_max
        self.buffer = []
        self.lock = threading.Lock()
        self.is_running = False
        self.thread = None
        self._sample_index = 0
        self._ai_task = None
        self._di_task = None

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
            import nidaqmx
        except ImportError as exc:
            raise RuntimeError("Brak biblioteki nidaqmx. Zainstaluj sterownik NI-DAQmx oraz pakiet Python nidaqmx.") from exc

        self._sample_index = 0
        self._ai_task = nidaqmx.Task()
        self._ai_task.ai_channels.add_ai_voltage_chan(
            self._full_channel(self.ai_channel),
            min_val=self.voltage_min,
            max_val=self.voltage_max,
        )

        if self.di_line.strip():
            self._di_task = nidaqmx.Task()
            self._di_task.di_channels.add_di_chan(self._full_channel(self.di_line))

        self.is_running = True
        self.thread = threading.Thread(target=self._acquisition_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None
        self._close_tasks()

    def _acquisition_loop(self):
        period = 1.0 / self.frequency
        while self.is_running:
            loop_start = time.monotonic()
            sample = self._read_sample()
            with self.lock:
                self.buffer.append(sample)

            elapsed = time.monotonic() - loop_start
            time.sleep(max(0.0, period - elapsed))

    def _read_sample(self):
        analog = float(self._ai_task.read())
        if self._di_task is not None:
            digital = int(bool(self._di_task.read()))
        else:
            digital = 0

        span = self.voltage_max - self.voltage_min
        potentiometer = (analog - self.voltage_min) / span if span else 0.0
        potentiometer = max(0.0, min(1.0, potentiometer))
        center = self.voltage_min + span / 2.0

        sample = {
            "time_s": self._sample_index / self.frequency,
            "ai_v": analog,
            "di": digital,
            "potentiometer": potentiometer,
            "proximity": int(analog > center),
            "switch": digital,
        }
        self._sample_index += 1
        return sample

    def get_samples(self):
        with self.lock:
            samples = list(self.buffer)
            self.buffer.clear()
        return samples

    def _full_channel(self, channel):
        channel = channel.strip()
        if "/" in channel:
            return channel
        return f"{self.device_name}/{channel}"

    def _close_tasks(self):
        for task_name in ("_di_task", "_ai_task"):
            task = getattr(self, task_name)
            if task is not None:
                try:
                    task.close()
                finally:
                    setattr(self, task_name, None)

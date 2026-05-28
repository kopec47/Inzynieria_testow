import csv
import datetime
import traceback
from collections import deque
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from daq_acquisition import AnalogAcquisition
from daq_generation import AnalogGeneration


class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("System testowy DAQ")
        self.root.report_callback_exception = self._handle_tk_exception

        self.daq = AnalogAcquisition()
        self.gen = AnalogGeneration()

        self.is_measuring = False
        self.auto_mode = tk.BooleanVar(value=False)
        self.plot_data = deque(maxlen=500)
        self.current_measure_data = []
        self.measure_stop_job = None
        self.auto_start_job = None
        self.update_job = None
        self.closing = False

        self._setup_ui()
        self.update_gui()

    def _handle_tk_exception(self, exc_type, exc_value, exc_tb):
        log_path = Path(__file__).resolve().parent / "daq_error.log"
        with log_path.open("a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.datetime.now().isoformat(sep=' ', timespec='seconds')}]\n")
            traceback.print_exception(exc_type, exc_value, exc_tb, file=f)
        try:
            messagebox.showerror("Blad aplikacji", f"{exc_type.__name__}: {exc_value}\n\nSzczegoly zapisano w daq_error.log")
        except tk.TclError:
            pass

    def _setup_ui(self):
        side_container = ttk.Frame(self.root)
        side_container.pack(side=tk.LEFT, fill=tk.Y)

        side_canvas = tk.Canvas(side_container, width=210, highlightthickness=0)
        side_scrollbar = ttk.Scrollbar(side_container, orient=tk.VERTICAL, command=side_canvas.yview)
        side_canvas.configure(yscrollcommand=side_scrollbar.set)
        side_canvas.pack(side=tk.LEFT, fill=tk.Y, expand=True)
        side_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        side = ttk.Frame(side_canvas, padding=10)
        side_window = side_canvas.create_window((0, 0), window=side, anchor=tk.NW)

        def update_scroll_region(_event=None):
            side_canvas.configure(scrollregion=side_canvas.bbox("all"))

        def update_side_width(event):
            side_canvas.itemconfigure(side_window, width=event.width)

        def on_mousewheel(event):
            if event.num == 4:
                side_canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                side_canvas.yview_scroll(1, "units")
            else:
                side_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        side.bind("<Configure>", update_scroll_region)
        side_canvas.bind("<Configure>", update_side_width)
        side_canvas.bind_all("<MouseWheel>", on_mousewheel)
        side_canvas.bind_all("<Button-4>", on_mousewheel)
        side_canvas.bind_all("<Button-5>", on_mousewheel)

        ttk.Label(side, text="Limit MIN [V]:").pack(anchor=tk.W)
        self.ent_min = ttk.Entry(side)
        self.ent_min.insert(0, "-4.0")
        self.ent_min.pack(fill=tk.X)

        ttk.Label(side, text="Limit MAX [V]:").pack(anchor=tk.W)
        self.ent_max = ttk.Entry(side)
        self.ent_max.insert(0, "4.0")
        self.ent_max.pack(fill=tk.X)

        ttk.Label(side, text="Zakres AI MIN [V]:").pack(anchor=tk.W)
        self.ent_range_min = ttk.Entry(side)
        self.ent_range_min.insert(0, "-10.0")
        self.ent_range_min.pack(fill=tk.X)

        ttk.Label(side, text="Zakres AI MAX [V]:").pack(anchor=tk.W)
        self.ent_range_max = ttk.Entry(side)
        self.ent_range_max.insert(0, "10.0")
        self.ent_range_max.pack(fill=tk.X)

        ttk.Label(side, text="Czestotliwosc [Hz]:").pack(anchor=tk.W)
        self.ent_freq = ttk.Entry(side)
        self.ent_freq.insert(0, "100")
        self.ent_freq.pack(fill=tk.X)

        ttk.Label(side, text="Dlugosc pomiaru [s]:").pack(anchor=tk.W)
        self.ent_duration = ttk.Entry(side)
        self.ent_duration.insert(0, "5")
        self.ent_duration.pack(fill=tk.X)

        ttk.Label(side, text="Przerwa auto [s]:").pack(anchor=tk.W)
        self.ent_auto_pause = ttk.Entry(side)
        self.ent_auto_pause.insert(0, "3")
        self.ent_auto_pause.pack(fill=tk.X)

        self.lbl_status = tk.Label(side, text="STATUS: STOP", bg="gray", fg="white", width=22)
        self.lbl_status.pack(pady=8, fill=tk.X)
        self.lbl_ai = ttk.Label(side, text="AI: -- V")
        self.lbl_ai.pack(anchor=tk.W)
        self.lbl_di = ttk.Label(side, text="DI: --")
        self.lbl_di.pack(anchor=tk.W)
        self.lbl_samples = ttk.Label(side, text="Probki pomiaru: 0")
        self.lbl_samples.pack(anchor=tk.W)
        self.lbl_auto = ttk.Label(side, text="Tryb: reczny")
        self.lbl_auto.pack(anchor=tk.W, pady=(0, 8))

        self.btn_start_daq = ttk.Button(side, text="START AKWIZYCJI", command=self.handle_start_daq)
        self.btn_start_daq.pack(fill=tk.X)
        self.btn_stop_daq = ttk.Button(side, text="STOP AKWIZYCJI", command=self.handle_stop_daq, state=tk.DISABLED)
        self.btn_stop_daq.pack(fill=tk.X, pady=2)
        ttk.Button(side, text="WYCZYSC WYKRES", command=self.clear_plot).pack(fill=tk.X, pady=2)

        self.btn_meas = ttk.Button(side, text="START POMIARU", command=self.toggle_meas, state=tk.DISABLED)
        self.btn_meas.pack(fill=tk.X, pady=5)
        ttk.Checkbutton(side, text="Tryb automatyczny", variable=self.auto_mode).pack(anchor=tk.W)

        ttk.Separator(side).pack(fill=tk.X, pady=8)
        ttk.Label(side, text="Wejscia testowe (symulacja)").pack(anchor=tk.W)
        self.lbl_pot = ttk.Label(side, text="Potencjometr: -- %")
        self.lbl_pot.pack(anchor=tk.W)
        self.lbl_prox = ttk.Label(side, text="Czujnik zblizeniowy: --")
        self.lbl_prox.pack(anchor=tk.W)
        self.lbl_switch = ttk.Label(side, text="Przelacznik: --")
        self.lbl_switch.pack(anchor=tk.W)

        ttk.Separator(side).pack(fill=tk.X, pady=8)
        ttk.Label(side, text="Generacja AO").pack(anchor=tk.W)
        self.combo_gen = ttk.Combobox(side, values=["sinusoida", "PWM"], state="readonly")
        self.combo_gen.current(0)
        self.combo_gen.pack(fill=tk.X)

        ttk.Label(side, text="Amplituda [V]:").pack(anchor=tk.W)
        self.ent_amp = ttk.Entry(side)
        self.ent_amp.insert(0, "5")
        self.ent_amp.pack(fill=tk.X)

        ttk.Label(side, text="Czestotliwosc AO [Hz]:").pack(anchor=tk.W)
        self.ent_gen_freq = ttk.Entry(side)
        self.ent_gen_freq.insert(0, "1")
        self.ent_gen_freq.pack(fill=tk.X)

        ttk.Label(side, text="Wypelnienie PWM [%]:").pack(anchor=tk.W)
        self.ent_duty = ttk.Entry(side)
        self.ent_duty.insert(0, "50")
        self.ent_duty.pack(fill=tk.X)

        self.lbl_ao = ttk.Label(side, text="AO: -- V")
        self.lbl_ao.pack(anchor=tk.W, pady=(4, 0))
        ttk.Button(side, text="START GEN", command=self.start_gen).pack(fill=tk.X)
        ttk.Button(side, text="STOP GEN", command=self.gen.stop).pack(fill=tk.X)

        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.line, = self.ax.plot([], [], "b-")
        self.ax.set_xlabel("Probka")
        self.ax.set_ylabel("AI [V]")
        self.ax.set_ylim(-10, 10)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    def handle_start_daq(self):
        try:
            self.daq.configure(
                frequency=self.ent_freq.get(),
                voltage_min=self.ent_range_min.get(),
                voltage_max=self.ent_range_max.get(),
            )
            self._apply_axis_range()
        except ValueError as exc:
            messagebox.showerror("Niepoprawna konfiguracja", str(exc))
            return

        self.plot_data.clear()
        self.current_measure_data = []
        self.lbl_samples.config(text="Probki pomiaru: 0")
        self.daq.start()
        self.btn_start_daq.config(state=tk.DISABLED)
        self.btn_stop_daq.config(state=tk.NORMAL)
        self.btn_meas.config(state=tk.NORMAL)
        self.lbl_status.config(bg="blue", text="STATUS: AKWIZYCJA")
        self.lbl_auto.config(text="Tryb: auto" if self.auto_mode.get() else "Tryb: reczny")

    def handle_stop_daq(self):
        self._cancel_jobs()
        if self.is_measuring:
            self._stop_meas(save=True, restart_auto=False)
        self.daq.stop()
        self.btn_start_daq.config(state=tk.NORMAL)
        self.btn_stop_daq.config(state=tk.DISABLED)
        self.btn_meas.config(state=tk.DISABLED, text="START POMIARU")
        self.lbl_status.config(bg="gray", text="STATUS: STOP")
        self.lbl_auto.config(text="Tryb: reczny")

    def clear_plot(self):
        self.plot_data.clear()
        self.line.set_data([], [])
        self.ax.set_xlim(0, 10)
        self.canvas.draw_idle()

    def start_gen(self):
        try:
            amplitude = float(self.ent_amp.get())
            frequency = float(self.ent_gen_freq.get())
            if self.combo_gen.get() == "sinusoida":
                self.gen.set_sine(amplitude, frequency)
            else:
                self.gen.set_pwm(amplitude, float(self.ent_duty.get()), frequency)
        except ValueError:
            messagebox.showerror("Niepoprawna konfiguracja", "Parametry AO musza byc liczbami.")
            return
        self.gen.start()

    def toggle_meas(self):
        if self.is_measuring:
            self._stop_meas(save=True)
            return

        try:
            duration = max(0.1, float(self.ent_duration.get()))
        except ValueError:
            messagebox.showerror("Niepoprawna konfiguracja", "Dlugosc pomiaru musi byc liczba.")
            return

        self.current_measure_data = []
        self.is_measuring = True
        self.btn_meas.config(text="STOP POMIARU")
        self.lbl_samples.config(text="Probki pomiaru: 0")
        self.lbl_status.config(bg="green", text="STATUS: POMIAR")
        self.lbl_auto.config(text="Tryb: pomiar")
        self.measure_stop_job = self.root.after(int(duration * 1000), lambda: self._stop_meas(save=True))

    def _stop_meas(self, save, restart_auto=True):
        self.is_measuring = False
        self.btn_meas.config(text="START POMIARU")
        if self.measure_stop_job is not None:
            try:
                self.root.after_cancel(self.measure_stop_job)
            except tk.TclError:
                pass
            self.measure_stop_job = None

        if save and self.current_measure_data:
            filename = self.save_data()
            self.lbl_auto.config(text=f"Zapisano: {filename.name}")
        elif save:
            self.lbl_auto.config(text="Brak probek do zapisu")

        if restart_auto and self.auto_mode.get() and self.daq.is_running:
            try:
                pause_s = max(0.1, float(self.ent_auto_pause.get()))
            except ValueError:
                pause_s = 3.0
            self.lbl_status.config(bg="orange", text="STATUS: PRZERWA AUTO")
            self.lbl_auto.config(text=f"Auto: kolejny pomiar za {pause_s:.1f} s")
            self.auto_start_job = self.root.after(int(pause_s * 1000), self.toggle_meas)
        elif self.daq.is_running:
            self.lbl_status.config(bg="blue", text="STATUS: AKWIZYCJA")
            self.lbl_auto.config(text="Tryb: auto" if self.auto_mode.get() else "Tryb: reczny")

    def save_data(self):
        out_dir = Path(__file__).resolve().parent
        fname = out_dir / f"data_{datetime.datetime.now().strftime('%H%M%S')}.csv"
        fieldnames = ["time_s", "ai_v", "di", "potentiometer", "proximity", "switch", "limit_ok"]
        with fname.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.current_measure_data)
        return fname

    def update_gui(self):
        if self.closing:
            return

        try:
            samples = self.daq.get_samples()
            if samples:
                try:
                    limit_min = float(self.ent_min.get())
                    limit_max = float(self.ent_max.get())
                except ValueError:
                    limit_min = float("-inf")
                    limit_max = float("inf")

                for sample in samples:
                    sample["limit_ok"] = limit_min <= sample["ai_v"] <= limit_max

                self.plot_data.extend(sample["ai_v"] for sample in samples)
                if self.is_measuring:
                    self.current_measure_data.extend(samples)
                    self.lbl_samples.config(text=f"Probki pomiaru: {len(self.current_measure_data)}")

                last = samples[-1]
                self._update_status(last)
                self._update_plot()

            if self.gen.is_running:
                self.lbl_ao.config(text=f"AO: {self.gen.get_value():.3f} V")
            else:
                self.lbl_ao.config(text="AO: -- V")
        except Exception:
            self._handle_tk_exception(*__import__("sys").exc_info())

        if not self.closing:
            try:
                self.update_job = self.root.after(100, self.update_gui)
            except tk.TclError:
                self.update_job = None

    def _update_status(self, sample):
        self.lbl_ai.config(text=f"AI: {sample['ai_v']:.3f} V")
        self.lbl_di.config(text=f"DI: {sample['di']}")
        self.lbl_pot.config(text=f"Potencjometr: {sample['potentiometer'] * 100:.1f} %")
        self.lbl_prox.config(text=f"Czujnik zblizeniowy: {sample['proximity']}")
        self.lbl_switch.config(text=f"Przelacznik: {sample['switch']}")

        if self.is_measuring:
            if sample["limit_ok"]:
                self.lbl_status.config(bg="green", text="STATUS: W LIMICIE")
            else:
                self.lbl_status.config(bg="red", text="STATUS: POZA LIMITEM")

    def _update_plot(self):
        self.line.set_data(range(len(self.plot_data)), self.plot_data)
        self.ax.set_xlim(0, max(10, len(self.plot_data)))
        self.canvas.draw_idle()

    def _apply_axis_range(self):
        low = float(self.ent_range_min.get())
        high = float(self.ent_range_max.get())
        padding = max(0.5, (high - low) * 0.05)
        self.ax.set_ylim(low - padding, high + padding)
        self.canvas.draw_idle()

    def _cancel_jobs(self):
        for job in (self.measure_stop_job, self.auto_start_job):
            if job is not None:
                try:
                    self.root.after_cancel(job)
                except tk.TclError:
                    pass
        self.measure_stop_job = None
        self.auto_start_job = None
        if self.update_job is not None:
            try:
                self.root.after_cancel(self.update_job)
            except tk.TclError:
                pass
            self.update_job = None

    def close(self):
        self.closing = True
        self._cancel_jobs()
        self.daq.stop()
        self.gen.stop()
        try:
            self.root.destroy()
        except tk.TclError:
            pass


if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.protocol("WM_DELETE_WINDOW", app.close)
    root.mainloop()

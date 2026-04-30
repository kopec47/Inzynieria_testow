import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import deque
import datetime
import csv

from daq_acquisition import AnalogAcquisition
from daq_generation import AnalogGeneration

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("System Testowy DAQ - Moduł 4")
        
        self.daq = AnalogAcquisition()
        self.gen = AnalogGeneration()
        
        self.is_measuring = False
        self.auto_mode = tk.BooleanVar(value=False)
        self.plot_data = deque(maxlen=100)
        self.current_measure_data = []

        self._setup_ui()
        self.update_gui()

    def _setup_ui(self):
        side = ttk.Frame(self.root, padding=10)
        side.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(side, text="Limit MIN [V]:").pack()
        self.ent_min = ttk.Entry(side)
        self.ent_min.insert(0, "-4.0")
        self.ent_min.pack()
        
        ttk.Label(side, text="Limit MAX [V]:").pack()
        self.ent_max = ttk.Entry(side)
        self.ent_max.insert(0, "4.0")
        self.ent_max.pack()
        
        self.lbl_status = tk.Label(side, text="STATUS: OK", bg="gray", width=15)
        self.lbl_status.pack(pady=10)

        self.btn_start_daq = ttk.Button(side, text="START AKWIZYCJI", command=self.handle_start_daq)
        self.btn_start_daq.pack(fill=tk.X)
        
        self.btn_stop_daq = ttk.Button(side, text="STOP AKWIZYCJI", command=self.handle_stop_daq, state=tk.DISABLED)
        self.btn_stop_daq.pack(fill=tk.X, pady=2)

        self.btn_meas = ttk.Button(side, text="START POMIARU", command=self.toggle_meas, state=tk.DISABLED)
        self.btn_meas.pack(fill=tk.X, pady=5)
        
        ttk.Checkbutton(side, text="Tryb Automatyczny", variable=self.auto_mode).pack()

        ttk.Label(side, text="\nGeneracja AO:").pack()
        self.combo_gen = ttk.Combobox(side, values=["sinusoida", "PWM"])
        self.combo_gen.current(0)
        self.combo_gen.pack()
        
        ttk.Button(side, text="START GEN", command=self.start_gen).pack(fill=tk.X)
        ttk.Button(side, text="STOP GEN", command=self.gen.stop).pack(fill=tk.X)

        self.fig, self.ax = plt.subplots(figsize=(5, 4))
        self.line, = self.ax.plot([], [], 'b-')
        self.ax.set_ylim(-10, 10)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    def handle_start_daq(self):
        self.daq.start()
        self.btn_start_daq.config(state=tk.DISABLED)
        self.btn_stop_daq.config(state=tk.NORMAL)
        self.btn_meas.config(state=tk.NORMAL)

    def handle_stop_daq(self):
        self.daq.stop()
        self.btn_start_daq.config(state=tk.NORMAL)
        self.btn_stop_daq.config(state=tk.DISABLED)
        self.btn_meas.config(state=tk.DISABLED)
        self.lbl_status.config(bg="gray", text="STATUS: OK")

    def start_gen(self):
        if self.combo_gen.get() == "sinusoida": 
            self.gen.set_sine(5, 1)
        else: 
            self.gen.set_pwm(5, 50)
        self.gen.start()

    def toggle_meas(self):
        if not self.is_measuring:
            self.current_measure_data = []
            self.is_measuring = True
            self.btn_meas.config(text="STOP POMIARU")
        else:
            self.is_measuring = False
            self.btn_meas.config(text="START POMIARU")
            self.save_data()
            if self.auto_mode.get():
                self.root.after(3000, self.toggle_meas)

    def save_data(self):
        fname = f"data_{datetime.datetime.now().strftime('%H%M%S')}.csv"
        with open(fname, 'w', newline='') as f:
            csv.writer(f).writerow(self.current_measure_data)

    def update_gui(self):
        samples = self.daq.get_samples()
        if samples:
            self.plot_data.extend(samples)
            if self.is_measuring: 
                self.current_measure_data.extend(samples)
            
            val = samples[-1]
            if val < float(self.ent_min.get()) or val > float(self.ent_max.get()):
                self.lbl_status.config(bg="red", text="POZA LIMITEM!")
            else:
                if self.is_measuring:
                    self.lbl_status.config(bg="green", text="W LIMICIE")

            self.line.set_data(range(len(self.plot_data)), self.plot_data)
            self.ax.set_xlim(0, len(self.plot_data))
            self.canvas.draw()
        self.root.after(100, self.update_gui)

if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.daq.stop(), app.gen.stop(), root.destroy()))
    root.mainloop()
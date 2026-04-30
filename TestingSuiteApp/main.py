import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import numpy as np  
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg 

class TestingSuiteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Modul 3 - podstawy gui w systemie testowym")
        self.root.geometry("1000x700")

        self.data = None #tu beda przechowywane dane

        self.setup_gui()

    def setup_gui(self):
        # Create a frame for buttons
        top_frame = tk.Frame(self.root)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        btn_load = tk.Button(top_frame, text="Load Data", command=self.load_data)
        btn_load.grid(row=0, column=0, padx=5)

        btn_plot = tk.Button(top_frame, text="Plot Data", command=self.plot_data)
        btn_plot.grid(row=0, column=1, padx=5)

        btn_calc = tk.Button(top_frame, text="Calculate Statistics", command=self.calculate_statistics)
        btn_calc.grid(row=0, column=2, padx=5)  

        self.log_var = tk.BooleanVar()
        chk_log = tk.Checkbutton(top_frame, text="log y?", variable=self.log_var, command=self.plot_data)
        chk_log.grid(row = 1, column = 0, sticky = "w", padx = 5)

        tk.Label(top_frame, text = "a").grid(row = 1, column = 2)
        self.entry_a = tk.Entry(top_frame, width = 10)
        self.entry_a.grid(row = 2, column = 2)

        tk.Label(top_frame, text = "b").grid(row = 1, column = 3)
        self.entry_b = tk.Entry(top_frame, width = 10)
        self.entry_b.grid(row = 2, column = 3)  

        mid_frame = tk.Frame(self.root)
        mid_frame.pack(side = tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)


        self.fig, self.ax = plt.subplots(figsize=(6, 5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=mid_frame)
        self.canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)   

        table_frame = tk.Frame(mid_frame)
        table_frame.pack(side=tk.RIGHT, fill=tk.Y, padx = 5)

        tk.Label(table_frame, text = "data").pack()

        self.tree = ttk.Treeview(table_frame, columns=("time", "value"), show="headings")
        self.tree.heading("time", text="Time")
        self.tree.heading("value", text="Amplitude")
        self.tree.column("time", width=80)
        self.tree.column("value", width=80)

        scroollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.Y)
        scroollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def load_data(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            try:
                self.df = pd.read_csv(file_path, sep=";")

                for item in self.tree.get_children():
                    self.tree.delete(item)

                for index, row in self.df.iterrows():
                    self.tree.insert("", "end", values=(row["time"], row["value"]))
                
                self.plot_data()
            except Exception as e:
                messagebox.showerror("blad", f"nie mozna odczytac dancych z pliku:{e}")


    def plot_data(self):
        if self.df is not None:
            self.ax.clear()
            self.ax.set_xlabel("Time")
            self.ax.set_ylabel("Amplitude")
            self.ax.grid(True)

            x = self.df["time"]
            y = self.df["value"]

            self.ax.scatter(x, y, s=10, label = "raw data")

            if self.log_var.get():
                self.ax.set_yscale("log")
            else:
                self.ax.set_yscale("linear")
            
            self.canvas.draw()

    def calculate_statistics(self):
        if self.df is not None:
            x = self.df["time"].values
            y = self.df["value"].values

            a, b = np.polyfit(x, y, 1)

            self.entry_a.delete(0, tk.END)
            self.entry_a.insert(0, f"{a:.4f}")

            self.entry_b.delete(0, tk.END)
            self.entry_b.insert(0, f"{b:.4f}")

            self.plot_data()
            y_pred = a * x + b
            self.ax.plot(x, y_pred, color="red", label=f'Fit: {a:.2f}x + {b:.2f}')
            self.ax.legend()
            self.canvas.draw()

        else:
            messagebox.showwarning("Brak danych", "Najpierw załaduj dane")

if __name__ == "__main__":
    root = tk.Tk()
    app = TestingSuiteApp(root)
    root.mainloop()      #  uruchomienie pętli głównej aplikacji
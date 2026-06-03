import sys
import queue
import multiprocessing
import threading
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

# Import our benchmarking modules
import module1
import module2
import module3
import module4
import module5

# ==========================================
# THREAD-SAFE CONSOLE REDIRECTION
# ==========================================
class ConsoleRedirector:
    def __init__(self, text_widget, root):
        self.text_widget = text_widget
        self.root = root
        self.queue = queue.Queue()
        self.update_widget()

    def write(self, string):
        self.queue.put(string)

    def flush(self):
        pass

    def update_widget(self):
        while not self.queue.empty():
            line = self.queue.get()
            self.text_widget.configure(state="normal")
            self.text_widget.insert("end", line)
            self.text_widget.see("end")
            self.text_widget.configure(state="disabled")
        self.root.after(100, self.update_widget)

# ==========================================
# GUI WRAPPER (CustomTkinter)
# ==========================================
class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Configuration
        self.title("Parallel Computing Demonstration Dashboard")
        self.geometry("1000x650")
        
        # Appearance 
        ctk.set_appearance_mode("Light")  
        ctk.set_default_color_theme("blue")
        
        # ------------------------
        # Left Frame: Controls
        # ------------------------
        self.left_frame = ctk.CTkFrame(self, corner_radius=20, width=380)
        self.left_frame.pack(side="left", pady=20, padx=(20, 10), fill="y")
        self.left_frame.pack_propagate(False)

        # Header
        self.header = ctk.CTkLabel(self.left_frame, text="Parallel Computing Suite", font=ctk.CTkFont(size=22, weight="bold"))
        self.header.pack(pady=(20, 5))
        
        self.subheader = ctk.CTkLabel(self.left_frame, text="Select a benchmark module.", font=ctk.CTkFont(size=13, slant="italic"))
        self.subheader.pack(pady=(0, 20))

        # Buttons
        self.btn_font = ctk.CTkFont(size=13, weight="bold")
        btn_padding = {"pady": 8, "padx": 20}
        
        self.btn1 = ctk.CTkButton(self.left_frame, text="Module 1: Parallelism Benchmark", 
                                  command=self.run_m1, font=self.btn_font, height=40, corner_radius=32)
        self.btn1.pack(**btn_padding, fill="x")

        self.btn2 = ctk.CTkButton(self.left_frame, text="Module 2: Processor Scheduling", 
                                  command=self.run_m2, font=self.btn_font, height=40, corner_radius=32, fg_color="#2b7a78", hover_color="#17252a")
        self.btn2.pack(**btn_padding, fill="x")

        self.btn3 = ctk.CTkButton(self.left_frame, text="Module 3: Bus Contention & Arbitration", 
                                  command=self.run_m3, font=self.btn_font, height=40, corner_radius=32, fg_color="#E07A5F", hover_color="#813405")
        self.btn3.pack(**btn_padding, fill="x")

        self.btn4 = ctk.CTkButton(self.left_frame, text="Module 4: Cache Coherence (MESI)", 
                                  command=self.run_m4, font=self.btn_font, height=40, corner_radius=32, fg_color="#3D5A80", hover_color="#293241")
        self.btn4.pack(**btn_padding, fill="x")

        self.btn5 = ctk.CTkButton(self.left_frame, text="Module 5: Performance Engine (Graphs)", 
                                  command=self.run_m5, font=self.btn_font, height=40, corner_radius=32, fg_color="#9B5DE5", hover_color="#7130B4")
        self.btn5.pack(**btn_padding, fill="x")
        
        # ------------------------
        # Right Frame: Console Output
        # ------------------------
        self.right_frame = ctk.CTkFrame(self, corner_radius=20)
        self.right_frame.pack(side="right", pady=20, padx=(10, 20), fill="both", expand=True)

        self.output_label = ctk.CTkLabel(self.right_frame, text="Presentation Output Console", font=ctk.CTkFont(size=14, weight="bold"))
        self.output_label.pack(pady=(10, 5), padx=10, anchor="w")

        self.console_textbox = ctk.CTkTextbox(self.right_frame, font=ctk.CTkFont(family="Consolas", size=12), wrap="word", state="disabled")
        self.console_textbox.pack(pady=(0, 10), padx=10, fill="both", expand=True)

        # Redirect standard output
        self.redirector = ConsoleRedirector(self.console_textbox, self)
        sys.stdout = self.redirector

    # ==========================================
    # EXECUTION HANDLERS
    # ==========================================
    def execute_with_loading(self, module_func, title):
        def worker():
            self.btn1.configure(state="disabled")
            self.btn2.configure(state="disabled")
            self.btn3.configure(state="disabled")
            self.btn4.configure(state="disabled")
            self.btn5.configure(state="disabled")
            
            try:
                module_func()
            finally:
                self.btn1.configure(state="normal")
                self.btn2.configure(state="normal")
                self.btn3.configure(state="normal")
                self.btn4.configure(state="normal")
                self.btn5.configure(state="normal")
                print(f"[{title} Execution Done.]\n")
                
        # Running in a separate thread so GUI doesn't freeze
        print(f"--- Running {title} ---")
        t = threading.Thread(target=worker)
        t.start()

    def run_m1(self):
        self.execute_with_loading(module1.run_module_1, "Module 1")

    def run_m2(self):
        self.execute_with_loading(module2.run_module_2, "Module 2")

    def run_m3(self):
        self.execute_with_loading(module3.run_module_3, "Module 3")

    def run_m4(self):
        self.execute_with_loading(module4.run_module_4, "Module 4")

    def run_m5(self):
        self.execute_with_loading(module5.run_module_5, "Module 5")

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    # freeze_support() is required in Windows when using the multiprocessing library
    multiprocessing.freeze_support() 
    app = App()
    
    # Optional: Catch window close to restore sys.stdout
    def on_closing():
        sys.stdout = sys.__stdout__
        app.destroy()
        
    app.protocol("WM_DELETE_WINDOW", on_closing)
    app.mainloop()

import customtkinter as ctk
import threading
import sys
import os
from reader_app import SignboardReaderApp

# Set default theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class TextRedirector(object):
    def __init__(self, widget, tag="stdout"):
        self.widget = widget
        self.tag = tag

    def write(self, str):
        self.widget.configure(state="normal")
        self.widget.insert("end", str)
        self.widget.see("end")
        self.widget.configure(state="disabled")

    def flush(self):
        pass

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Signboard Reader AI")
        self.geometry("600x600") # Increased height for console
        # self.resizable(False, False) # Allow resizing logic handles it
        
        # Grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0) # Header
        self.grid_rowconfigure(1, weight=0) # Controls
        self.grid_rowconfigure(2, weight=0) # Status
        self.grid_rowconfigure(3, weight=1) # Console (Expandable)

        # Header
        self.header_frame = ctk.CTkFrame(self, corner_radius=10)
        self.header_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        
        self.label_title = ctk.CTkLabel(self.header_frame, text="Real-Time Signboard Reader", 
                                      font=ctk.CTkFont(size=24, weight="bold"))
        self.label_title.pack(padx=20, pady=20)

        # Main Controls
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=1, column=0, padx=20, sticky="nsew")
        
        self.btn_start = ctk.CTkButton(self.main_frame, text="START DETECTION", 
                                     font=ctk.CTkFont(size=16, weight="bold"),
                                     height=50, corner_radius=25,
                                     command=self.start_detection)
        self.btn_start.pack(pady=10, fill="x")

        self.btn_settings = ctk.CTkButton(self.main_frame, text="SETTINGS", 
                                        font=ctk.CTkFont(size=14),
                                        height=40, fg_color="gray", hover_color="darkgray",
                                        command=self.open_settings)
        self.btn_settings.pack(pady=10, fill="x")
        
        self.btn_console = ctk.CTkButton(self.main_frame, text="HIDE CONSOLE", 
                                        font=ctk.CTkFont(size=12),
                                        height=30, fg_color="#444444", hover_color="#333333",
                                        command=self.toggle_console)
        self.btn_console.pack(pady=5, fill="x")

        # Status
        self.label_status = ctk.CTkLabel(self, text="Status: Ready", text_color="gray")
        self.label_status.grid(row=2, column=0, pady=10)

        # Console Frame
        self.console_frame = ctk.CTkFrame(self)
        self.console_frame.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="nsew")
        
        self.console_text = ctk.CTkTextbox(self.console_frame, activate_scrollbars=True)
        self.console_text.pack(expand=True, fill="both", padx=5, pady=5)
        self.console_text.configure(state="disabled")
        
        # Redirect stdout
        sys.stdout = TextRedirector(self.console_text)
        sys.stderr = TextRedirector(self.console_text) # Capture errors too

        # Logic
        self.reader_thread = None
        self.reader_app = None
        self.is_running = False
        self.console_visible = True

    def toggle_console(self):
        if self.console_visible:
            self.console_frame.grid_remove() # Hide
            self.btn_console.configure(text="SHOW CONSOLE")
            self.geometry("600x450") # Shrink window
        else:
            self.console_frame.grid() # Show
            self.btn_console.configure(text="HIDE CONSOLE")
            self.geometry("600x600") # Expand window
        self.console_visible = not self.console_visible

    def start_detection(self):
        if not self.is_running:
            self.is_running = True
            self.label_status.configure(text="Status: Running...", text_color="#00FF00")
            self.btn_start.configure(text="STOP DETECTION", fg_color="#FF4444", hover_color="#CC0000")
            
            # Initialize App
            print("Initializing Reader App...")
            self.reader_app = SignboardReaderApp()
            
            # Run in thread
            self.reader_thread = threading.Thread(target=self.run_reader_safe, daemon=True)
            self.reader_thread.start()
        else:
            self.stop_detection()

    def stop_detection(self):
        if self.is_running and self.reader_app:
            self.reader_app.stop()
            self.is_running = False
            self.label_status.configure(text="Status: Stopped", text_color="gray")
            self.btn_start.configure(text="START DETECTION", fg_color=("#3B8ED0", "#1F6AA5"), hover_color=("#36719F", "#144870")) # Reset to default blue

    def run_reader_safe(self):
        try:
            self.reader_app.run()
        except Exception as e:
            print(f"Error in reader thread: {e}")
        finally:
            # When thread finishes (e.g. user pressed 'q' in opencv window), update UI
            self.after(0, self.stop_detection)

    def open_settings(self):
        # Create a Toplevel window
        settings_window = ctk.CTkToplevel(self)
        settings_window.title("Settings")
        settings_window.geometry("300x200")
        settings_window.attributes("-topmost", True)
        
        label = ctk.CTkLabel(settings_window, text="Appearance Mode", font=ctk.CTkFont(size=14, weight="bold"))
        label.pack(pady=10)
        
        option_menu = ctk.CTkOptionMenu(settings_window, values=["Dark", "Light", "System"],
                                      command=self.change_appearance_mode)
        option_menu.set(ctk.get_appearance_mode())
        option_menu.pack(pady=10)
        
        label_info = ctk.CTkLabel(settings_window, text="System Voices (TTS)", font=ctk.CTkFont(size=14, weight="bold"))
        label_info.pack(pady=10)
        
        btn_check_voice = ctk.CTkButton(settings_window, text="List Voices in Console",
                                      command=self.list_voices)
        btn_check_voice.pack(pady=5)

    def change_appearance_mode(self, new_appearance_mode):
        ctk.set_appearance_mode(new_appearance_mode)

    def list_voices(self):
        import check_voices
        check_voices.list_voices()

if __name__ == "__main__":
    app = App()
    app.mainloop()

import customtkinter as ctk
import serial
import serial.tools.list_ports
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import csv
import time
from tkinter import PhotoImage  # Import PhotoImage


class ArduinoGUI:
    def __init__(self, master):
        self.master = master
        master.title("Arduino GUI")
        master.geometry("1000x700")
        master.configure(bg='#f0f0f0')  # Light grey background

        # Create GUI widgets
        self.port_frame = ctk.CTkFrame(master)
        self.port_frame.pack(fill='x', pady=10)

        self.label = ctk.CTkLabel(self.port_frame, text="Select Port:", font=('Helvetica', 12, 'bold'))
        self.label.pack(side='left', padx=10)

        self.port_var = ctk.StringVar()
        self.port_menu = ctk.CTkOptionMenu(self.port_frame, values=self.get_ports(), variable=self.port_var)
        self.port_menu.pack(side='left', padx=10)

        self.connect_button = ctk.CTkButton(self.port_frame, text="Connect", command=self.connect_arduino,
                                           font=('Helvetica', 12, 'bold'), fg_color='#007bff', text_color='white')
        self.connect_button.pack(side='left', padx=10)

        self.disconnect_button = ctk.CTkButton(self.port_frame, text="Disconnect", command=self.disconnect_arduino,
                                              font=('Helvetica', 12, 'bold'), fg_color='#007bff',
                                              text_color='white')
        self.disconnect_button.pack(side='left', padx=10)

        self.data_frame = ctk.CTkFrame(master)
        self.data_frame.pack(fill='x', pady=10)

        sensor_labels = ["Humidity:", "Temperature:", "Angle:", "Intensity:"]
        self.data_labels = []
        for i, label_text in enumerate(sensor_labels):
            label = ctk.CTkLabel(self.data_frame, text=label_text, font=('Helvetica', 12, 'bold'))
            label.grid(row=0, column=i, padx=20, pady=5)  # Decreased padding between labels
            data_label = ctk.CTkLabel(self.data_frame, text="", font=('Helvetica', 16, 'bold'))  # Increased font size for data labels
            data_label.grid(row=1, column=i, padx=20, pady=5)  # Decreased padding between data labels
            self.data_labels.append(data_label)

        self.plot_frame = ctk.CTkFrame(master)
        self.plot_frame.pack(fill='both', expand=True)

        self.fig, self.axs = plt.subplots(2, 2, figsize=(8, 6))  # Increased vertical distance between graphs
        self.canvas = FigureCanvasTkAgg(self.fig, self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

        # Initialize lines for each plot
        self.lines = []
        for i in range(2):
            for j in range(2):
                line, = self.axs[i, j].plot([], [])
                self.lines.append(line)

        self.x_data = [[] for _ in range(4)]
        self.y_data = [[] for _ in range(4)]

        self.ser = None
        self.csv_writer = None

        # Add scale widgets
        self.scale_frame = ctk.CTkFrame(master)
        self.scale_frame.pack(fill='x', pady=10)

        self.scale1_label = ctk.CTkLabel(self.scale_frame, text="Scale 1:", font=('Helvetica', 12, 'bold'))
        self.scale1_label.pack(side='left', padx=10)

        self.scale1 = ctk.CTkSlider(self.scale_frame, from_=0, to=100, orientation='horizontal')
        self.scale1.pack(side='left', padx=10)

        self.scale2_label = ctk.CTkLabel(self.scale_frame, text="Scale 2:", font=('Helvetica', 12, 'bold'))
        self.scale2_label.pack(side='left', padx=10)

        self.scale2 = ctk.CTkSlider(self.scale_frame, from_=0, to=100, orientation='horizontal')
        self.scale2.pack(side='left', padx=10)

        self.send_button = ctk.CTkButton(self.scale_frame, text="Send", command=self.send_scale_values,
                                          font=('Helvetica', 12, 'bold'), fg_color='#007bff', text_color='white')
        self.send_button.pack(side='left', padx=10)

        # Add save data button
        self.save_data_button = ctk.CTkButton(self.scale_frame, text="Save Data",
                                              command=self.save_data_to_csv,
                                              font=('Helvetica', 12, 'bold'),
                                              fg_color='#007bff', text_color='white')
        self.save_data_button.pack(side='left', padx=10)

        # Add color theme selection
        self.color_theme_frame = ctk.CTkFrame(master)
        self.color_theme_frame.pack(fill='x', pady=10)

        self.color_theme_label = ctk.CTkLabel(self.color_theme_frame, text="Select Theme:",
                                              font=('Helvetica', 12, 'bold'))
        self.color_theme_label.pack(side='left', padx=10)

        self.color_theme_var = ctk.StringVar()
        self.color_theme_menu = ctk.CTkOptionMenu(self.color_theme_frame, values=["Light", "Dark"],
                                                 variable=self.color_theme_var)
        self.color_theme_menu.pack(side='left', padx=10)

        self.color_theme_var.trace("w", self.change_color_theme)

        # Configure rows and columns to expand with window size
        self.data_frame.grid_columnconfigure(0, weight=1)
        self.data_frame.grid_columnconfigure(1, weight=1)
        self.data_frame.grid_columnconfigure(2, weight=1)
        self.data_frame.grid_columnconfigure(3, weight=1)
        self.data_frame.grid_rowconfigure(0, weight=1)
        self.data_frame.grid_rowconfigure(1, weight=1)

    def get_ports(self):
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]
        return port_list

    def connect_arduino(self):
        port = self.port_var.get()
        self.ser = serial.Serial(port, 9600, timeout=1)
        self.update_gui()

    def disconnect_arduino(self):
        if self.ser:
            self.ser.close()
            self.ser = None

    def update_gui(self):
        if self.ser:
            line = self.ser.readline().decode('utf-8').strip()
            if line:
                humidity, temperature, angle, intensity = self.parse_data(line)
                data_values = [humidity, temperature, angle, intensity]

                for i, value in enumerate(data_values):
                    self.data_labels[i].configure(text=value)
                    self.x_data[i].append(time.time())  # Use time.time() to record timestamps
                    self.y_data[i].append(float(value))
                    self.lines[i].set_data(self.x_data[i], self.y_data[i])
                    row = i // 2
                    col = i % 2
                    self.axs[row, col].relim()
                    self.axs[row, col].autoscale_view()
                    self.axs[row, col].set_xlim(max(self.x_data[i][0], time.time() - 100),
                                                time.time())  # Set x-axis limits
                self.canvas.draw()
        self.master.after(100, self.update_gui)

    def parse_data(self, data):
        # Extract the values after the letters H, T, B, and L
        parts = data.split('H')[1].split('T')
        humidity = parts[0]
        parts = parts[1].split('B')
        temperature = parts[0]
        parts = parts[1].split('L')
        angle = parts[0]
        intensity = parts[1]
        return humidity, temperature, angle, intensity

    def send_scale_values(self):
        if self.ser:
            value1 = self.scale1.get() if self.scale1.get() else 0
            value2 = self.scale2.get() if self.scale2.get() else 0
            self.ser.write(f"{value1},{value2}".encode())  # Send the values separated by a comma

    def save_data_to_csv(self):
        if self.ser:
            try:
                # Create a new CSV file with a timestamp in the filename
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                file_path = f"sensor_data_{timestamp}.csv"

                # Get scale values
                scale_value1 = self.scale1.get()
                scale_value2 = self.scale2.get()

                # Write data to the CSV file
                with open(file_path, 'w', newline='') as csv_file:
                    csv_writer = csv.writer(csv_file)
                    csv_writer.writerow(
                        ["Timestamp", "Humidity", "Temperature", "Angle", "Intensity", "Scale 1",
                         "Scale 2"])  # Write header
                    for i in range(len(self.x_data[0])):  # Assuming all x_data have the same length
                        timestamp = time.strftime("%Y-%m-%d %H:%M:%S",
                                                 time.localtime(self.x_data[0][i]))
                        row = [timestamp, self.y_data[0][i], self.y_data[1][i], self.y_data[2][i],
                               self.y_data[3][i], scale_value1,
                               scale_value2]  # Add scale values to the row
                        csv_writer.writerow(row)

                print(f"Data saved to {file_path}")
            except Exception as e:
                print(f"Error saving data: {e}")
        else:
            print("Not connected to Arduino.")

    def change_color_theme(self, *args):
        selected_theme = self.color_theme_var.get()
        if selected_theme == "Light":
            ctk.set_appearance_mode("light")
        elif selected_theme == "Dark":
            ctk.set_appearance_mode("dark")


root = ctk.CTk()
my_gui = ArduinoGUI(root)
root.mainloop()

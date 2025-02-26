import csv
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from concurrent.futures import ThreadPoolExecutor
import dns.resolver
import time
import threading

# Global variable to store CSV data cache
csv_data_cache = None

# Initialize the ThreadPoolExecutor
executor = ThreadPoolExecutor(max_workers=5)

# Function to clear DNS cache (if applicable)
def clear_cache():
    # Implement cache clearing logic here
    pass

# Function to read the CSV file and extract necessary information
def read_csv_file(file_path):
    global csv_data_cache
    try:
        with open(file_path, mode='r') as file:
            reader = csv.DictReader(file)
            data = [row for row in reader]
            csv_data_cache = {"file_path": file_path, "data": data}
            return data
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read the CSV file: {e}")
        return []

# Function to validate the CSV file's structure
def validate_csv_structure(data):
    if len(data) == 0:
        messagebox.showerror("Error", "CSV file is empty.")
        return False
    required_columns = ['Name', 'DNSRecord']
    for row in data:
        if not all(col in row for col in required_columns):
            messagebox.showerror("Error", "CSV file is missing required columns.")
            return False
    return True

# Function to handle DNS updates
def update_dns(file_path, result_table, progress_bar, update_a, update_cname, a_count_label, cname_count_label, total_count_label):
    if csv_data_cache is None:
        messagebox.showerror("Error", "No CSV file selected.")
        return

    data = csv_data_cache["data"]
    total_records = len(data)
    progress_bar['maximum'] = total_records
    success_count_a = 0
    success_count_cname = 0

    for idx, row in enumerate(data):
        progress_bar['value'] = idx + 1
        result_table.insert("", "end", values=(row['Name'], row['DNSRecord'], "In Progress"))

        try:
            if update_a and row['DNSRecord'] == 'A':
                # Add DNS A record update logic here
                success_count_a += 1
            elif update_cname and row['DNSRecord'] == 'CNAME':
                # Add DNS CNAME record update logic here
                success_count_cname += 1

            result_table.item(result_table.get_children()[idx], values=(row['Name'], row['DNSRecord'], "Success"))
        except Exception as e:
            result_table.item(result_table.get_children()[idx], values=(row['Name'], row['DNSRecord'], f"Failed: {e}"))
        
        # Update progress
        progress_bar.update_idletasks()

    # Update the counts in the labels
    a_count_label.config(text=f"A Records: {success_count_a}")
    cname_count_label.config(text=f"CNAME Records: {success_count_cname}")
    total_count_label.config(text=f"Total Records: {total_records}")

# Function to handle CSV file selection and reading
def select_csv_file():
    file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
    if file_path:
        data = read_csv_file(file_path)
        if validate_csv_structure(data):
            messagebox.showinfo("Info", f"CSV file '{file_path}' loaded successfully.")

# Function to update the DNS records asynchronously
def start_dns_update(result_table, progress_bar, update_a, update_cname, a_count_label, cname_count_label, total_count_label):
    if csv_data_cache is None:
        messagebox.showerror("Error", "No CSV file loaded.")
        return

    # Submit the DNS update task to the thread pool for asynchronous execution
    executor.submit(update_dns, csv_data_cache["file_path"], result_table, progress_bar, update_a, update_cname, a_count_label, cname_count_label, total_count_label)

# GUI Setup
def create_gui():
    root = tk.Tk()
    root.title("DNS Update Tool")

    frame = ttk.Frame(root, padding="10")
    frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    select_file_button = ttk.Button(frame, text="Select CSV File", command=select_csv_file)
    select_file_button.grid(row=0, column=0, padx=5, pady=5)

    result_table = ttk.Treeview(frame, columns=("Name", "DNSRecord", "Status"), show="headings", height=10)
    result_table.grid(row=1, column=0, columnspan=3, padx=5, pady=5)

    result_table.heading("Name", text="Name")
    result_table.heading("DNSRecord", text="DNS Record")
    result_table.heading("Status", text="Status")

    progress_bar = ttk.Progressbar(frame, length=200, mode="determinate")
    progress_bar.grid(row=2, column=0, padx=5, pady=5)

    update_button = ttk.Button(frame, text="Start DNS Update", command=lambda: start_dns_update(result_table, progress_bar, update_a_var.get(), update_cname_var.get(), a_count_label, cname_count_label, total_count_label))
    update_button.grid(row=3, column=0, padx=5, pady=5)

    update_a_var = tk.BooleanVar(value=True)
    update_cname_var = tk.BooleanVar(value=True)

    a_checkbox = ttk.Checkbutton(frame, text="Update A Records", variable=update_a_var)
    a_checkbox.grid(row=4, column=0, padx=5, pady=5)

    cname_checkbox = ttk.Checkbutton(frame, text="Update CNAME Records", variable=update_cname_var)
    cname_checkbox.grid(row=4, column=1, padx=5, pady=5)

    # Labels for success counts
    a_count_label = ttk.Label(frame, text="A Records: 0")
    a_count_label.grid(row=5, column=0, padx=5, pady=5)

    cname_count_label = ttk.Label(frame, text="CNAME Records: 0")
    cname_count_label.grid(row=5, column=1, padx=5, pady=5)

    total_count_label = ttk.Label(frame, text="Total Records: 0")
    total_count_label.grid(row=5, column=2, padx=5, pady=5)

    root.mainloop()

if __name__ == "__main__":
    create_gui()

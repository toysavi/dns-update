import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import threading
import pythoncom
import win32com.client

def fetch_dns_zones():
    pythoncom.CoInitialize()
    try:
        dns_server = "localhost"
        dnscom = win32com.client.Dispatch("MicrosoftDNS.Server")
        dns_zones = dnscom.GetZones()
        return [zone.Name for zone in dns_zones]
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch DNS zones: {e}")
        return []
    finally:
        pythoncom.CoUninitialize()

def update_dns(zone_name, record_name, record_type, new_value):
    pythoncom.CoInitialize()
    try:
        dns_server = "localhost"
        dnscom = win32com.client.Dispatch("MicrosoftDNS.Server")
        dns_zone = dnscom.GetZone(zone_name)
        existing_records = dns_zone.EnumRecords(record_name, 0)
        
        # Delete existing record if necessary
        for record in existing_records:
            if record.RecordType == record_type:
                record.Delete()
                break
        
        # Create new record
        dns_zone.CreateInstanceFromPropertyData(dns_server, record_name, record_type, 600, new_value)
        messagebox.showinfo("Success", f"Updated {record_name} in {zone_name} to {new_value}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to update DNS record: {e}")
    finally:
        pythoncom.CoUninitialize()

def process_csv(file_path, dns_zone):
    try:
        df = pd.read_csv(file_path, dtype=str)
        for index, row in df.iterrows():
            update_dns(dns_zone, row['RecordName'], int(row['RecordType']), row['NewValue'])
    except Exception as e:
        messagebox.showerror("Error", f"Error processing CSV: {e}")

def open_file_dialog():
    file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
    if file_path:
        selected_zone = dns_zone_combobox.get()
        if not selected_zone:
            messagebox.showwarning("Warning", "Please select a DNS zone before proceeding.")
            return
        threading.Thread(target=process_csv, args=(file_path, selected_zone), daemon=True).start()

def show_main_window():
    global dns_zone_combobox
    root = tk.Tk()
    root.title("DNS Updater")
    
    tk.Label(root, text="Select DNS Zone:").pack(pady=5)
    dns_zone_combobox = ttk.Combobox(root, state="readonly")
    dns_zone_combobox.pack(pady=5)
    
    dns_zones = fetch_dns_zones()
    dns_zone_combobox['values'] = dns_zones
    if dns_zones:
        dns_zone_combobox.current(0)
    
    tk.Button(root, text="Select CSV File", command=open_file_dialog).pack(pady=10)
    root.mainloop()

if __name__ == "__main__":
    show_main_window()

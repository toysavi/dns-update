import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import threading
import pythoncom
import win32com.client
import logging

# Configure logging
logging.basicConfig(filename="dns_updater.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def fetch_dns_zones():
    pythoncom.CoInitialize()
    try:
        dnscom = win32com.client.Dispatch("MicrosoftDNS.Server")
        dns_zones = dnscom.GetZones()
        return [zone.Name for zone in dns_zones]
    except Exception as e:
        logging.error(f"Failed to fetch DNS zones: {e}")
        messagebox.showerror("Error", f"Failed to fetch DNS zones: {e}")
        return []
    finally:
        pythoncom.CoUninitialize()

def update_dns(zone_name, record_name, record_type, new_value):
    pythoncom.CoInitialize()
    try:
        dnscom = win32com.client.Dispatch("MicrosoftDNS.Server")
        dns_zone = dnscom.GetZone(zone_name)
        existing_records = dns_zone.EnumRecords(record_name, 0)
        
        if existing_records:
            for record in existing_records:
                if record.RecordType == record_type:
                    record.Delete()
                    break
        
        dns_zone.CreateInstanceFromPropertyData("localhost", record_name, record_type, 600, new_value)
        logging.info(f"Updated {record_name} in {zone_name} to {new_value}")
        messagebox.showinfo("Success", f"Updated {record_name} in {zone_name} to {new_value}")
    except Exception as e:
        logging.error(f"Failed to update DNS record: {e}")
        messagebox.showerror("Error", f"Failed to update DNS record: {e}")
    finally:
        pythoncom.CoUninitialize()

def process_csv(file_path, dns_zone, progress_bar, start_button):
    try:
        df = pd.read_csv(file_path, dtype=str)
        required_columns = {'RecordName', 'RecordType', 'NewValue'}
        
        if not required_columns.issubset(df.columns):
            messagebox.showerror("Error", "CSV file is missing required columns: RecordName, RecordType, NewValue")
            return
        
        start_button.config(state=tk.DISABLED)
        progress_bar['maximum'] = len(df)
        
        for index, row in df.iterrows():
            update_dns(dns_zone, row['RecordName'], int(row['RecordType']), row['NewValue'])
            progress_bar['value'] = index + 1
            root.update_idletasks()
        
        messagebox.showinfo("Success", "All DNS records updated successfully!")
    except Exception as e:
        logging.error(f"Error processing CSV: {e}")
        messagebox.showerror("Error", f"Error processing CSV: {e}")
    finally:
        start_button.config(state=tk.NORMAL)
        progress_bar['value'] = 0

def open_file_dialog():
    file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
    if file_path:
        selected_zone = dns_zone_combobox.get()
        if not selected_zone:
            messagebox.showwarning("Warning", "Please select a DNS zone before proceeding.")
            return
        
        threading.Thread(target=process_csv, args=(file_path, selected_zone, progress_bar, start_button), daemon=True).start()

def show_main_window():
    global root, dns_zone_combobox, progress_bar, start_button
    root = tk.Tk()
    root.title("DNS Updater")
    root.geometry("400x250")
    root.eval('tk::PlaceWindow . center')
    
    tk.Label(root, text="Select DNS Zone:").pack(pady=5)
    dns_zone_combobox = ttk.Combobox(root, state="readonly")
    dns_zone_combobox.pack(pady=5)
    
    dns_zones = fetch_dns_zones()
    dns_zone_combobox['values'] = dns_zones
    if dns_zones:
        dns_zone_combobox.current(0)
    
    start_button = tk.Button(root, text="Select CSV File", command=open_file_dialog)
    start_button.pack(pady=10)
    
    progress_bar = ttk.Progressbar(root, orient=tk.HORIZONTAL, length=300, mode='determinate')
    progress_bar.pack(pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    show_main_window()

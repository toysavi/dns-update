import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import threading
import os

# Function to update A and CNAME records in AD DNS
def update_dns(csv_file, dns_zone, result_label):
    try:
        # Delay import of pythoncom and win32com.client until needed
        import pythoncom
        import win32com.client

        # Connect to WMI DNS Client
        pythoncom.CoInitialize()
        dns_client = win32com.client.GetObject("winmgmts:\\\\.\\root\\MicrosoftDNS")
        
        # Read CSV file
        df = pd.read_csv(csv_file)

        # Confirm before applying changes
        confirm = messagebox.askyesno("Confirm Update", f"Update {len(df)} DNS records?")
        if not confirm:
            return
        
        success_count = 0
        failed_count = 0

        for _, row in df.iterrows():
            record_type = row["RecordType"].strip().upper()
            record_name = row["RecordName"].strip()
            new_value = row["NewValue"].strip()

            try:
                if record_type == "A":
                    # Update A Record (Change IP Address)
                    existing_records = dns_client.ExecQuery(
                        f"SELECT * FROM MicrosoftDNS_AType WHERE ContainerName='{dns_zone}' AND OwnerName='{record_name}'"
                    )

                    if len(existing_records) > 0:
                        # Delete old record
                        for record in existing_records:
                            record.Delete_()

                    # Create new A record
                    dns_client.Get("MicrosoftDNS_AType").CreateInstanceFromPropertyData(
                        dns_zone, record_name, 600, new_value
                    )

                elif record_type == "CNAME":
                    # Update CNAME Record
                    existing_records = dns_client.ExecQuery(
                        f"SELECT * FROM MicrosoftDNS_CNAMEType WHERE ContainerName='{dns_zone}' AND OwnerName='{record_name}'"
                    )

                    if len(existing_records) > 0:
                        # Delete old record
                        for record in existing_records:
                            record.Delete_()

                    # Create new CNAME record
                    dns_client.Get("MicrosoftDNS_CNAMEType").CreateInstanceFromPropertyData(
                        dns_zone, record_name, 600, new_value
                    )

                else:
                    raise Exception(f"Invalid RecordType: {record_type}")

                success_count += 1

            except Exception as e:
                print(f"Failed to update {record_name}: {e}")
                failed_count += 1

        result_label.config(text=f"Update Complete\nSuccess: {success_count}\nFailed: {failed_count}")

    except Exception as e:
        result_label.config(text=f"Error: {str(e)}")
    finally:
        pythoncom.CoUninitialize()

# Function to browse and select CSV
def browse_file(result_label):
    file_path = filedialog.askopenfilename(initialdir=os.path.expanduser("~"), filetypes=[("CSV Files", "*.csv")])
    if file_path:
        # Get DNS Zone from the entry field
        dns_zone = dns_zone_entry.get().strip() or "example.com"  # Default to "example.com" if empty
        threading.Thread(target=update_dns, args=(file_path, dns_zone, result_label)).start()

# GUI Setup
root = tk.Tk()
root.title("DNS Updater (A & CNAME Records)")

# DNS Zone Entry
tk.Label(root, text="Enter DNS Zone (optional, default is 'example.com'):").pack(pady=10)
dns_zone_entry = tk.Entry(root)
dns_zone_entry.pack(pady=5)

# File selection and update buttons
tk.Label(root, text="Select a CSV file to update A & CNAME records:").pack(pady=10)
tk.Button(root, text="Browse CSV", command=lambda: browse_file(result_label)).pack(pady=5)

# Result label
result_label = tk.Label(root, text="", justify="left")
result_label.pack(pady=10)

# Exit button
tk.Button(root, text="Exit", command=root.quit).pack(pady=5)

# Start the GUI
root.mainloop()

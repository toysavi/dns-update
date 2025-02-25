import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import threading
import os

# Function to fetch DNS zones (alias names)
def fetch_dns_zones():
    try:
        # Delay import of pythoncom and win32com.client until needed
        import pythoncom
        import win32com.client

        # Connect to WMI DNS Client
        pythoncom.CoInitialize()
        dns_client = win32com.client.GetObject("winmgmts:\\\\.\\root\\MicrosoftDNS")

        # Fetch A and CNAME records
        a_records = dns_client.ExecQuery("SELECT OwnerName FROM MicrosoftDNS_AType")
        cname_records = dns_client.ExecQuery("SELECT OwnerName FROM MicrosoftDNS_CNAMEType")

        # Extract unique alias names
        dns_zones = set(record.OwnerName for record in a_records)
        dns_zones.update(record.OwnerName for record in cname_records)

        return sorted(dns_zones)

    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch DNS zones: {str(e)}")
        return []

    finally:
        pythoncom.CoUninitialize()

# Function to update A and CNAME records in AD DNS
def update_dns(csv_file, dns_zone, result_table):
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
        
        for _, row in df.iterrows():
            record_type = row["RecordType"].strip().upper()
            record_name = row["RecordName"].strip()
            new_value = row["NewValue"].strip()
            status = "Unknown"

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
                    status = "Successful"

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
                    status = "Successful"

                else:
                    raise Exception(f"Invalid RecordType: {record_type}")

            except Exception as e:
                print(f"Failed to update {record_name}: {e}")
                status = f"Failed: {e}"

            # Update result table
            result_table.insert("", "end", values=(record_type, record_name, "", new_value, status))

    except Exception as e:
        messagebox.showerror("Error", f"Error: {str(e)}")
    finally:
        pythoncom.CoUninitialize()

# Function to browse and select CSV
def browse_file(result_table):
    file_path = filedialog.askopenfilename(initialdir="C:\\", filetypes=[("CSV Files", "*.csv")])
    if file_path:
        # Get DNS Zone from the combobox
        dns_zone = dns_zone_combobox.get().strip() or "example.com"  # Default to "example.com" if empty
        threading.Thread(target=update_dns, args=(file_path, dns_zone, result_table)).start()

# GUI Setup
root = tk.Tk()
root.title("DNS Updater (A & CNAME Records)")

# DNS Zone Combobox
tk.Label(root, text="Select DNS Zone:").pack(pady=10)
dns_zone_combobox = ttk.Combobox(root, values=fetch_dns_zones())
dns_zone_combobox.pack(pady=5)

# File selection and update buttons
tk.Label(root, text="Select a CSV file to update A & CNAME records:").pack(pady=10)
tk.Button(root, text="Browse CSV", command=lambda: browse_file(result_table)).pack(pady=5)

# Result table
columns = ("Record Type", "Source Name", "Source IP", "Destination Name", "Destination IP", "Status")
result_table = ttk.Treeview(root, columns=columns, show="headings")
for col in columns:
    result_table.heading(col, text=col)
result_table.pack(pady=10, fill="both", expand=True)

# Exit button
tk.Button(root, text="Exit", command=root.quit).pack(pady=5)

# Start the GUI
root.mainloop()

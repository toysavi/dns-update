import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import win32com.client

# DNS Zone Name (Change if necessary)
DNS_ZONE = "example.com"

# Function to update A and CNAME records in AD DNS
def update_dns(csv_file):
    try:
        # Connect to WMI DNS Client
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
                        f"SELECT * FROM MicrosoftDNS_AType WHERE ContainerName='{DNS_ZONE}' AND OwnerName='{record_name}'"
                    )

                    if len(existing_records) > 0:
                        # Delete old record
                        for record in existing_records:
                            record.Delete_()

                    # Create new A record
                    dns_client.Get("MicrosoftDNS_AType").CreateInstanceFromPropertyData(
                        DNS_ZONE, record_name, 600, new_value
                    )

                elif record_type == "CNAME":
                    # Update CNAME Record
                    existing_records = dns_client.ExecQuery(
                        f"SELECT * FROM MicrosoftDNS_CNAMEType WHERE ContainerName='{DNS_ZONE}' AND OwnerName='{record_name}'"
                    )

                    if len(existing_records) > 0:
                        # Delete old record
                        for record in existing_records:
                            record.Delete_()

                    # Create new CNAME record
                    dns_client.Get("MicrosoftDNS_CNAMEType").CreateInstanceFromPropertyData(
                        DNS_ZONE, record_name, 600, new_value
                    )

                else:
                    raise Exception(f"Invalid RecordType: {record_type}")

                success_count += 1

            except Exception as e:
                print(f"Failed to update {record_name}: {e}")
                failed_count += 1

        messagebox.showinfo("Update Complete", f"Success: {success_count}, Failed: {failed_count}")

    except Exception as e:
        messagebox.showerror("Error", str(e))

# Function to browse and select CSV
def browse_file():
    file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
    if file_path:
        update_dns(file_path)

# GUI Setup
root = tk.Tk()
root.title("DNS Updater (A & CNAME Records)")

tk.Label(root, text="Select a CSV file to update A & CNAME records:").pack(pady=10)
tk.Button(root, text="Browse CSV", command=browse_file).pack(pady=5)
tk.Button(root, text="Exit", command=
root.quit).pack(pady=5)

root.mainloop()

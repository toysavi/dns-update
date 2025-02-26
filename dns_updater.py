import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import threading
import os

# Cache for DNS zones and CSV data
dns_zones_cache = None
csv_data_cache = None

# Function to fetch DNS zones (alias names)
def fetch_dns_zones():
    global dns_zones_cache
    if dns_zones_cache is not None:
        return dns_zones_cache

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

        dns_zones_cache = sorted(dns_zones)
        return dns_zones_cache

    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch DNS zones: {str(e)}")
        return []

    finally:
        pythoncom.CoUninitialize()

# Function to read CSV file and cache the data
def read_csv_file(file_path):
    global csv_data_cache
    if csv_data_cache is not None and csv_data_cache["file_path"] == file_path:
        return csv_data_cache["data"]

    try:
        df = pd.read_csv(file_path)
        csv_data_cache = {"file_path": file_path, "data": df}
        
        # Update result table to show CSV upload success message
        return df
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read CSV file: {str(e)}")
        return pd.DataFrame()

# Function to update A and CNAME records in AD DNS
def update_dns(result_table, progress_bar, update_a, update_cname, a_count_label, cname_count_label, total_count_label):
    try:
        # Delay import of pythoncom and win32com.client until needed
        import pythoncom
        import win32com.client

        # Connect to WMI DNS Client
        pythoncom.CoInitialize()
        dns_client = win32com.client.GetObject("winmgmts:\\\\.\\root\\MicrosoftDNS")

        # Read CSV file
        if csv_data_cache is None:
            messagebox.showerror("Error", "No CSV file loaded.")
            return
        
        df = csv_data_cache["data"]
        
        # Confirm before applying changes
        confirm = messagebox.askyesno("Confirm Update", f"Update {len(df)} DNS records?")
        if not confirm:
            return

        total_records = len(df)
        progress_bar["maximum"] = total_records

        a_count = 0
        cname_count = 0

        for index, row in df.iterrows():
            src_alias = row["Src Alias"].strip()
            src_point_to = row["Src Point to"].strip()
            des_alias = row["Des. Alias"].strip()
            des_point_to = row["Des. Point to"].strip()
            status = "Unknown"

            try:
                if update_a:
                    # Update A Record (Change IP Address)
                    existing_records = dns_client.ExecQuery(
                        f"SELECT * FROM MicrosoftDNS_AType WHERE OwnerName='{src_alias}'"
                    )

                    if len(existing_records) > 0:
                        # Delete old record
                        for record in existing_records:
                            record.Delete_()

                    # Create new A record for destination
                    dns_client.Get("MicrosoftDNS_AType").CreateInstanceFromPropertyData(
                        des_alias.split('.')[-2], des_alias, 600, des_point_to
                    )
                    status = "Successful"
                    a_count += 1

                elif update_cname:
                    # Update CNAME Record
                    existing_records = dns_client.ExecQuery(
                        f"SELECT * FROM MicrosoftDNS_CNAMEType WHERE OwnerName='{src_alias}'"
                    )

                    if len(existing_records) > 0:
                        # Delete old record
                        for record in existing_records:
                            record.Delete_()

                    # Create new CNAME record for destination
                    dns_client.Get("MicrosoftDNS_CNAMEType").CreateInstanceFromPropertyData(
                        des_alias.split('.')[-2], des_alias, 600, des_point_to
                    )
                    status = "Successful"
                    cname_count += 1

                else:
                    raise Exception(f"Invalid RecordType: A or CNAME")

            except Exception as e:
                print(f"Failed to update {src_alias}: {e}")
                status = f"Failed: {e}"

            # Update result table
            result_table.insert("", "end", values=(src_alias, src_point_to, des_alias, des_point_to, status))
            progress_bar["value"] = index + 1

            # Update count labels
            a_count_label.config(text=f"A Records: {a_count}")
            cname_count_label.config(text=f"CNAME Records: {cname_count}")
            total_count_label.config(text=f"Total Records: {a_count + cname_count}")

    except Exception as e:
        messagebox.showerror("Error", f"Error: {str(e)}")
    finally:
        pythoncom.CoUninitialize()

# Function to browse and select CSV
def browse_file(result_table):
    def read_file_in_background(file_path):
        global csv_data_cache
        csv_data_cache = {"file_path": file_path, "data": read_csv_file(file_path)}
        
        # Update result table to show CSV upload success message after reading
        result_table.insert("", "end", values=("CSV is uploaded", "", "", "", ""))
        messagebox.showinfo("File Selected", f"Selected file: {file_path}")

    file_path = filedialog.askopenfilename(initialdir="C:\\", filetypes=[("CSV Files", "*.csv")])
    if file_path:
        threading.Thread(target=read_file_in_background, args=(file_path,)).start()

# Function to apply DNS updates
def apply_updates(result_table, progress_bar, update_a, update_cname, a_count_label, cname_count_label, total_count_label):
    if csv_data_cache is None:
        messagebox.showerror("Error", "No CSV file selected.")
        return
    threading.Thread(target=update_dns, args=(result_table, progress_bar, update_a, update_cname, a_count_label, cname_count_label, total_count_label)).start()

# Function to clear the information
def clear_information(result_table, progress_bar, update_a, update_cname, a_count_label, cname_count_label, total_count_label):
    global csv_data_cache
    csv_data_cache = None
    result_table.delete(*result_table.get_children())
    progress_bar["value"] = 0
    update_a.set(False)
    update_cname.set(False)
    a_count_label.config(text="A Records: 0")
    cname_count_label.config(text="CNAME Records: 0")
    total_count_label.config(text="Total Records: 0")
    messagebox.showinfo("Cleared", "Information cleared.")

# Function to filter the result table based on the search query
def filter_results(search_query, result_table):
    for row in result_table.get_children():
        values = result_table.item(row, "values")
        if any(search_query.lower() in str(value).lower() for value in values):
            result_table.item(row, tags=("match",))
        else:
            result_table.item(row, tags=("no_match",))
    result_table.tag_configure("match", background="white")
    result_table.tag_configure("no_match", background="gray")

# Function to fetch DNS zones when the combobox is clicked
def on_combobox_click(event):
    threading.Thread(target=lambda: dns_zone_combobox.config(values=fetch_dns_zones())).start()

# Function to show the main application window
def show_main_window():
    # GUI Setup
    root = tk.Tk()
    root.title("DNS Updater (A & CNAME Records)")

    # Frame for file selection and DNS zone
    file_frame = tk.Frame(root)
    file_frame.pack(pady=10)

    # File selection button
    tk.Label(file_frame, text="Select a CSV file to update A & CNAME records:").grid(row=0, column=0, padx=5)
    result_table = ttk.Treeview(file_frame, columns=("Src Alias", "Src Point to", "Des. Alias", "Des. Point to", "Status"), show="headings")
    result_table.heading("Src Alias", text="Src Alias")
    result_table.heading("Src Point to", text="Src Point to")
    result_table.heading("Des. Alias", text="Des. Alias")
    result_table.heading("Des. Point to", text="Des. Point to")
    result_table.heading("Status", text="Status")
    result_table.grid(row=1, column=0, columnspan=2, pady=5)

    # Progress bar
    progress_frame = tk.Frame(root)
    progress_frame.pack(pady=10)
    progress_bar = ttk.Progressbar(progress_frame, length=200, mode="determinate")
    progress_bar.grid(row=0, column=0, padx=5)

    # Buttons for browsing and applying changes
    browse_button = tk.Button(file_frame, text="Browse", command=lambda: browse_file(result_table))
    browse_button.grid(row=0, column=1, padx=5)

    # A record and CNAME record checkboxes
    update_a = tk.BooleanVar()
    update_cname = tk.BooleanVar()

    # Apply updates button
    apply_button = tk.Button(root, text="Apply Update", command=lambda: apply_updates(result_table, progress_bar, update_a, update_cname, a_count_label, cname_count_label, total_count_label))
    apply_button.pack(pady=10)

    # Clear Information button
    clear_button = tk.Button(root, text="Clear Information", command=lambda: clear_information(result_table, progress_bar, update_a, update_cname, a_count_label, cname_count_label, total_count_label))
    clear_button.pack(pady=10)

    # Add search functionality
    search_frame = tk.Frame(root)
    search_frame.pack(pady=10)
    tk.Label(search_frame, text="Search:").grid(row=0, column=0, padx=5)
    search_entry = tk.Entry(search_frame)
    search_entry.grid(row=0, column=1, padx=5)
    search_entry.bind("<KeyRelease>", lambda event: filter_results(event.widget.get(), result_table))

    # Count labels
    count_frame = tk.Frame(root)
    count_frame.pack(pady=5)
    a_count_label = tk.Label(count_frame, text="A Records: 0")
    a_count_label.grid(row=0, column=0, padx=5)
    cname_count_label = tk.Label(count_frame, text="CNAME Records: 0")
    cname_count_label.grid(row=0, column=1, padx=5)
    total_count_label = tk.Label(count_frame, text="Total Records: 0")
    total_count_label.grid(row=0, column=2, padx=5)

    root.mainloop()

if __name__ == "__main__":
    show_main_window()

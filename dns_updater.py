import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import threading
import os

# Event to signal when the main window is ready
main_window_ready = threading.Event()

# Function to show the loading screen
def show_loading_screen():
    loading_root = tk.Tk()
    loading_root.title("Loading")
    loading_label = tk.Label(loading_root, text="Loading, please wait...", font=("Helvetica", 16))
    loading_label.pack(pady=40, padx=40)

    # Center the loading screen
    loading_root.update_idletasks()
    width = loading_root.winfo_width()
    height = loading_root.winfo_height()
    x = (loading_root.winfo_screenwidth() // 2) - (width // 2)
    y = (loading_root.winfo_screenheight() // 2) - (height // 2)
    loading_root.geometry(f'{width}x{height}+{x}+{y}')

    def wait_for_main_window():
        main_window_ready.wait()
        loading_root.destroy()
        show_main_window()

    threading.Thread(target=wait_for_main_window).start()
    loading_root.mainloop()

# Show the loading screen
threading.Thread(target=show_loading_screen).start()

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
        return df
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read CSV file: {str(e)}")
        return pd.DataFrame()

# Function to update A and CNAME records in AD DNS
def update_dns(csv_file, result_table, progress_bar, progress_label, update_a, update_cname, a_count_label, cname_count_label, total_count_label):
    try:
        # Delay import of pythoncom and win32com.client until needed
        import pythoncom
        import win32com.client

        # Connect to WMI DNS Client
        pythoncom.CoInitialize()
        dns_client = win32com.client.GetObject("winmgmts:\\\\.\\root\\MicrosoftDNS")
        
        # Read CSV file
        df = read_csv_file(csv_file)

        # Confirm before applying changes
        confirm = messagebox.askyesno("Confirm Update", f"Update {len(df)} DNS records?")
        if not confirm:
            return
        
        total_records = len(df)
        progress_bar["maximum"] = total_records

        a_count = 0
        cname_count = 0

        for index, row in df.iterrows():
            record_type = row["RecordType"].strip().upper()
            record_name = row["RecordName"].strip()
            new_value = row["NewValue"].strip()
            status = "Unknown"

            try:
                if record_type == "A" and update_a:
                    # Update A Record (Change IP Address)
                    existing_records = dns_client.ExecQuery(
                        f"SELECT * FROM MicrosoftDNS_AType WHERE OwnerName='{record_name}'"
                    )

                    if len(existing_records) > 0:
                        # Delete old record
                        for record in existing_records:
                            record.Delete_()

                    # Create new A record
                    dns_client.Get("MicrosoftDNS_AType").CreateInstanceFromPropertyData(
                        record_name.split('.')[-2], record_name, 600, new_value
                    )
                    status = "Successful"
                    a_count += 1

                elif record_type == "CNAME" and update_cname:
                    # Update CNAME Record
                    existing_records = dns_client.ExecQuery(
                        f"SELECT * FROM MicrosoftDNS_CNAMEType WHERE OwnerName='{record_name}'"
                    )

                    if len(existing_records) > 0:
                        # Delete old record
                        for record in existing_records:
                            record.Delete_()

                    # Create new CNAME record
                    dns_client.Get("MicrosoftDNS_CNAMEType").CreateInstanceFromPropertyData(
                        record_name.split('.')[-2], record_name, 600, new_value
                    )
                    status = "Successful"
                    cname_count += 1

                else:
                    raise Exception(f"Invalid RecordType: {record_type}")

            except Exception as e:
                print(f"Failed to update {record_name}: {e}")
                status = f"Failed: {e}"

            # Update result table
            result_table.insert("", "end", values=(record_type, record_name, "", new_value, status))
            progress_bar["value"] = index + 1

            # Update count labels
            a_count_label.config(text=f"A Records: {a_count}")
            cname_count_label.config(text=f"CNAME Records: {cname_count}")
            total_count_label.config(text=f"Total Records: {a_count + cname_count}")

            # Update progress label
            progress_label.config(text=f"Progress: {int((index + 1) / total_records * 100)}%")

    except Exception as e:
        messagebox.showerror("Error", f"Error: {str(e)}")
    finally:
        pythoncom.CoUninitialize()

# Function to browse and select CSV
def browse_file():
    def read_file_in_background(file_path):
        global csv_data_cache
        csv_data_cache = {"file_path": file_path, "data": read_csv_file(file_path)}
        messagebox.showinfo("File Selected", f"Selected file: {file_path}")

    file_path = filedialog.askopenfilename(initialdir="C:\\", filetypes=[("CSV Files", "*.csv")])
    if file_path:
        threading.Thread(target=read_file_in_background, args=(file_path,)).start()

# Function to apply DNS updates
def apply_updates(result_table, progress_bar, progress_label, update_a, update_cname, a_count_label, cname_count_label, total_count_label):
    if csv_data_cache is None:
        messagebox.showerror("Error", "No CSV file selected.")
        return
    threading.Thread(target=update_dns, args=(csv_data_cache["file_path"], result_table, progress_bar, progress_label, update_a, update_cname, a_count_label, cname_count_label, total_count_label)).start()

# Function to clear the information
def clear_information(result_table, progress_bar, progress_label, update_a, update_cname, a_count_label, cname_count_label, total_count_label):
    global csv_data_cache
    csv_data_cache = None
    result_table.delete(*result_table.get_children())
    progress_bar["value"] = 0
    progress_label.config(text="Progress: 0%")
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
    tk.Button(file_frame, text="Browse CSV", command=browse_file).grid(row=0, column=1, padx=5)

    # DNS Zone Combobox
    tk.Label(file_frame, text="Select DNS Zone:").grid(row=0, column=2, padx=5)
    dns_zone_combobox = ttk.Combobox(file_frame)
    dns_zone_combobox.grid(row=0, column=3, padx=5)
    dns_zone_combobox.bind("<Button-1>", on_combobox_click)

    # Frame for checkboxes, apply, clear, and search box
    frame = tk.Frame(root)
    frame.pack(pady=10)

    # Checkboxes for selecting record types to update
    update_a = tk.BooleanVar()
    update_cname = tk.BooleanVar()
    tk.Checkbutton(frame, text="Update A Records", variable=update_a).grid(row=0, column=0, padx=5)
    tk.Checkbutton(frame, text="Update CNAME Records", variable=update_cname).grid(row=0, column=1, padx=5)

    # Apply and Clear buttons
    tk.Button(frame, text="Apply Updates", command=lambda: apply_updates(result_table, progress_bar, progress_label, update_a, update_cname, a_count_label, cname_count_label, total_count_label)).grid(row=0, column=2, padx=5)
    tk.Button(frame, text="Clear", command=lambda: clear_information(result_table, progress_bar, progress_label, update_a, update_cname, a_count_label, cname_count_label, total_count_label)).grid(row=0, column=3, padx=5)

    # Search box
    tk.Label(frame, text="Search:").grid(row=0, column=4, padx=5)
    search_entry = tk.Entry(frame)
    search_entry.grid(row=0, column=5, padx=5)
    search_entry.bind("<KeyRelease>", lambda event: filter_results(search_entry.get(), result_table))

    # Result table
    columns = ("Record Type", "Source Name", "Source IP", "Destination Name", "Destination IP", "Status")
    result_table = ttk.Treeview(root, columns=columns, show="headings")
    for col in columns:
        result_table.heading(col, text=col)
    result_table.pack(pady=10, fill="both", expand=True)

    # Progress bar and count labels
    progress_frame = tk.Frame(root)
    progress_frame.pack(pady=10)
    progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", length=400, mode="determinate")
    progress_bar.grid(row=0, column=0, padx=5)
    progress_label = tk.Label(progress_frame, text="Progress: 0%")
    progress_label.grid(row=0, column=1, padx=5)
    a_count_label = tk.Label(progress_frame, text="A Records: 0")
    a_count_label.grid(row=0, column=2, padx=5)
    cname_count_label = tk.Label(progress_frame, text="CNAME Records: 0")
    cname_count_label.grid(row=0, column=3, padx=5)
    total_count_label = tk.Label(progress_frame, text="Total Records: 0")
    total_count_label.grid(row=0, column=4, padx=5)

    # Exit button
    tk.Button(root, text="Exit", command=root.quit).pack(pady=5)

    # Signal that the main window is ready
    main_window_ready.set()

    # Start the GUI
    root.mainloop()

# Initialize the main application in the background
threading.Thread(target=show_main_window).start()

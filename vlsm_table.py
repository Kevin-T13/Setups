import pandas as pd
import ipaddress
import tkinter as tk
from tkinter import messagebox
from pandastable import Table

# --- Configuration ---
# Global variables for the root window and theme
# Using a slightly more modern font and padding for better aesthetics
FONT_TITLE = ("Roboto", 16, "bold")
FONT_LABEL = ("Roboto", 12)
PADDING = 15
TABLE_WIDTH = 1200
TABLE_HEIGHT = 600



def skuska():
    """
    Performs Variable Length Subnet Masking (VLSM) calculations, 
    creates a DataFrame of the results, and displays it in a new window.
    """
    ip_input = entry.get().strip()
    hosts_raw = hosts.get("1.0", tk.END).strip()

    if not ip_input or not hosts_raw:
        messagebox.showerror("Input error", "Enter the default IP address/prefix and the list of desired hosts.")
        return

    # 1. Input Validation and Parsing
    try:
        # Initial validation: Check if the base network is valid
        current_network = ipaddress.ip_network(ip_input, strict=False)
    except ValueError:
        messagebox.showerror("Input error", f"Invalid IP address or prefix format: {ip_input}. Use format like 192.168.1.0/24.")
        return

    try:
        # Parse hosts input (split by newlines or commas) and convert to integers
        hosts_list = [int(h.strip()) for h in hosts_raw.replace(',', '\n').splitlines() if h.strip()]
        
        # VLSM requires sorting in descending order of hosts needed
        # Tieto zoradené hodnoty sa použijú na výpočet a budú sa zobrazovať v tabuľke.
        hosts_list.sort(reverse=True)
    except ValueError:
        messagebox.showerror("Input error", "The requested hosts must be a list of positive integers. (napr. 100, 50, 20).")
        return

    if not hosts_list:
        messagebox.showerror("Input error", "You have not entered any valid hosts.")
        return

    results = []
    
    # Track the available IP space
    current_ip = current_network.network_address

    # 2. VLSM Calculation Loop
    for requested_hosts in hosts_list:
        # Calculate the smallest power of 2 that holds requested_hosts + 2 (for network and broadcast)
        # hosts needed = requested_hosts + 2
        
        if requested_hosts + 2 > current_network.num_addresses:
            messagebox.showerror("Allocation error", 
                                 f"Unable to allocate {requested_hosts} hosts. The remaining IP space is insufficient or the initial network is too small.")
            break
            
        # Determine the number of address bits needed: 2^n >= requested_hosts + 2
        bits_needed = (requested_hosts + 1).bit_length()
        
        # Calculate the new prefix length
        new_prefix = 32 - bits_needed

        # Check if the requested prefix is longer than the initial prefix (VLSM cannot increase the mask)
        if new_prefix < current_network.prefixlen:
             messagebox.showerror("Prefix error", 
                                 f"Requested number of hosts ({requested_hosts} hosts) need prefix /{new_prefix}, which is less than the initial network prefix /{current_network.prefixlen}. VLSM only allows *smaller* subnets, not larger than the initial network.")
             return
             
        # Create the new subnet based on the current available IP and the calculated prefix
        try:
            # Construct the subnet string: e.g., '192.168.1.0/25'
            subnet_str = f"{current_ip}/{new_prefix}"
            new_subnet = ipaddress.ip_network(subnet_str, strict=False)

            # Check for overlap/out-of-bounds relative to the original network
            if new_subnet.broadcast_address > current_network.broadcast_address:
                messagebox.showerror("Allocation error", 
                                     f"Unable to allocate {requested_hosts} hosts. Additional subnet required ({new_subnet.with_prefixlen}) would exceed the initial network boundary ({ip_input}).")
                break

            # Calculate details for the result table
            net_ip_with_prefix = str(new_subnet.with_prefixlen)
            mask = str(new_subnet.netmask)
            first_host = str(new_subnet.network_address + 1)
            last_host = str(new_subnet.broadcast_address - 1)
            broadcast = str(new_subnet.broadcast_address)
            usable_ips = len(list(new_subnet.hosts())) # Number of hosts (total - 2)

            # Check if there are usable hosts (i.e., prefix is not /31 or /32)
            if usable_ips < 1:
                 # This should ideally not happen due to the bit_length calculation, but as a safeguard:
                 usable_ips = 0
                 first_host = "N/A"
                 last_host = "N/A"


            # Používame slovenské hlavičky pre stĺpce
            results.append({
                'Requested': requested_hosts,
                'Net IP + prefix': net_ip_with_prefix,
                'Mask': mask,
                'First host': first_host,
                'Last host': last_host,
                'Broadcast': broadcast,
                'Usable IP': usable_ips,
            })
            
            # Update the current available IP for the next iteration
            current_ip = new_subnet.broadcast_address + 1

        except ValueError as e:
            messagebox.showerror("Calculation error", f"A calculation error occurred: {e}")
            break


    
    root2 = tk.Toplevel(root)
    root2.title("The resulting VLSM subnet table")
    root2.geometry(f"{TABLE_WIDTH}x{TABLE_HEIGHT}")
    
    label_title = tk.Label(root2, text=f"VLSM Subnetting for the initial network: {ip_input}", font=FONT_TITLE, fg="#0056b3")
    label_title.pack(pady=10)
    
    df = pd.DataFrame(results)
    
    if not df.empty:
        df["Requested"] = df["Requested"].astype("Int64")
        df["Usable IP"] = df["Usable IP"].astype("Int64")

    
    # If no results were generated (e.g., due to an early break/error)
    if df.empty:
         # Používame slovenské hlavičky pre chybovú tabuľku
         df = pd.DataFrame({
            'Requested': ['N/A'],
            'Net IP + prefix': ['N/A'],
            'Mask': ['N/A'],
            'First host': ['N/A'],
            'Last host': ['N/A'],
            'Broadcast': ['N/A'],
            'Usable IP': ['Error: See the previous message.']
        })
    
    frame = tk.Frame(root2)
    frame.pack(fill='both', expand=True, padx=20, pady=10)
    
    table = Table(frame, dataframe=df, showtoolbar=False, showstatusbar=False)
    table.show()
    # Style the table for better readability
    table.align = 'center'
    table.cellbackgr = '#f4f7f9'
    table.thefont = ('Roboto', 10)
    table.redraw()


# --- Main GUI Setup ---
root = tk.Tk()
root.title("VLSM IPv4 Subnet Calculator")
root.geometry("550x350")
root.configure(bg='#e6eef4')
root.resizable(False, False)

tk.Label(root, text="VLSM IPv4 Subnet Calculator", font=("Roboto", 20, "bold"), bg='#e6eef4', fg='#0056b3').pack(pady=15)

tk.Label(root, text="1. Enter the initial IP network (napr. 192.168.1.0/24)", font=FONT_LABEL, bg='#e6eef4', fg='#333').pack()
entry = tk.Entry(root, width=35, font=('Roboto', 12), bd=2, relief=tk.FLAT)
entry.pack(pady=5, padx=PADDING)
entry.insert(0, "192.168.1.0/24") # Default value for convenience

tk.Label(root, text="2. Enter the desired guests (one per line or separated by comma)", font=FONT_LABEL, bg='#e6eef4', fg='#333').pack()
hosts = tk.Text(root, height=3, width=35, font=('Roboto', 12), bd=2, relief=tk.FLAT)
hosts.pack(pady=5, padx=PADDING)
hosts.insert("1.0", "100\n50\n20") # Default values for convenience

button = tk.Button(
    root, 
    text="Generate VLSM Subnets Table", 
    command=skuska,
    bg='#007bff', 
    fg='white', 
    font=('Roboto', 14, 'bold'),
    cursor="hand2",
    padx=15,
    pady=8
)
button.pack(pady=20)

root.mainloop()
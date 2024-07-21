import subprocess
import re
import string
import random

# The registry path for network interfaces in Windows
network_interface_reg_path = r"HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\Class\\{4d36e972-e325-11ce-bfc1-08002be10318}"

# Regular expression to match transport names, e.g., {AF1B45DB-B5D4-46D0-B4EA-3E18FA49BF5F}
transport_name_regex = re.compile(r"{.+}")

# Regular expression to match MAC addresses, e.g., AA:BB:CC:DD:EE:FF
mac_address_regex = re.compile(r"([A-F0-9]{2}[:-]){5}([A-F0-9]{2})")

def get_random_mac_address():
    """Generate and return a random MAC address in the format of WINDOWS."""
    # Generate a string of hexadecimal digits (0-9, A-F)
    uppercased_hexdigits = ''.join(set(string.hexdigits.upper()))
    # Construct a random MAC address
    return random.choice(uppercased_hexdigits) + random.choice("24AE") + ":" + ":".join("".join(random.sample(uppercased_hexdigits, k=2)) for _ in range(5))

def clean_mac(mac):
    """Remove non-hexadecimal characters from a MAC address and convert it to uppercase."""
    # Remove characters not in hexadecimal digits and uppercase the result
    return "".join(c for c in mac if c in string.hexdigits).upper()

def get_connected_adapters_mac_address():
    """Get a list of connected network adapters with their MAC addresses and transport names."""
    connected_adapters_mac = []
    try:
        # Execute 'getmac' command to list network adapters
        for potential_mac in subprocess.check_output("getmac").decode().splitlines():
            # Search for MAC address and transport name in the output
            mac_address = mac_address_regex.search(potential_mac)
            transport_name = transport_name_regex.search(potential_mac)
            if mac_address and transport_name:
                # Append valid MAC address and transport name to the list
                connected_adapters_mac.append((mac_address.group(), transport_name.group()))
    except subprocess.CalledProcessError as e:
        # Handle errors in executing the 'getmac' command
        print(f"Failed to get connected adapters: {e}")
    return connected_adapters_mac

def change_mac_address(adapter_transport_name, new_mac_address):
    """Change the MAC address of a specified adapter."""
    try:
        # Query the registry to find the interfaces
        output = subprocess.check_output(f"reg QUERY " +  network_interface_reg_path.replace("\\\\", "\\")).decode()
        # Find interfaces matching the registry path pattern
        for interface in re.findall(rf"{network_interface_reg_path}\\\d+", output):
            adapter_index = int(interface.split("\\")[-1])
            # Query the registry for the specific interface
            interface_content = subprocess.check_output(f"reg QUERY {interface.strip()}").decode()
            if adapter_transport_name in interface_content:
                # Change the MAC address in the registry
                changing_mac_output = subprocess.check_output(f"reg add {interface} /v NetworkAddress /d {new_mac_address} /f").decode()
                print(changing_mac_output)
                break
        return adapter_index
    except subprocess.CalledProcessError as e:
        # Handle errors in changing the MAC address
        print(f"Failed to change MAC address: {e}")
        return None

def disable_adapter(adapter_index):
    """Disable the network adapter specified by index."""
    try:
        # Use 'wmic' command to disable the adapter
        disable_output = subprocess.check_output(f"wmic path win32_networkadapter where index={adapter_index} call disable").decode()
        return disable_output
    except subprocess.CalledProcessError as e:
        # Handle errors in disabling the adapter
        print(f"Failed to disable adapter: {e}")
        return None

def enable_adapter(adapter_index):
    """Enable the network adapter specified by index."""
    try:
        # Use 'wmic' command to enable the adapter
        enable_output = subprocess.check_output(f"wmic path win32_networkadapter where index={adapter_index} call enable").decode()
        return enable_output
    except subprocess.CalledProcessError as e:
        # Handle errors in enabling the adapter
        print(f"Failed to enable adapter: {e}")
        return None

def get_user_adapter_choice(connected_adapters_mac):
    """Prompt the user to select which adapter to change."""
    print("Available adapters:")
    # List all available adapters with their MAC address and transport name
    for i, (mac, transport_name) in enumerate(connected_adapters_mac, 1):
        print(f"{i}. MAC: {mac}, Transport Name: {transport_name}")
    # Get the user's choice and return the selected adapter
    choice = int(input("Select adapter to change (1-{}): ".format(len(connected_adapters_mac))))
    return connected_adapters_mac[choice - 1]

if __name__ == "__main__":
    import argparse
    # Set up argument parsing for command-line options
    parser = argparse.ArgumentParser(description="MACSPOOF (｡•̀ᴗ-)✧")
    parser.add_argument("-r", "--random", action="store_true", help="Whether to generate a random MAC address or not")
    parser.add_argument("-m", "--mac", help="The new MAC you want to change to")
    args = parser.parse_args()

    # Determine the new MAC address based on command-line arguments
    if args.random:
        new_mac_address = get_random_mac_address()
    elif args.mac:
        new_mac_address = clean_mac(args.mac)

    # Get a list of connected adapters and prompt the user for selection
    connected_adapters_mac = get_connected_adapters_mac_address()
    old_mac_address, target_transport_name = get_user_adapter_choice(connected_adapters_mac)
    print("[*] Old MAC address:", old_mac_address)
    # Change the MAC address of the selected adapter
    adapter_index = change_mac_address(target_transport_name, new_mac_address)
    if adapter_index is not None:
        print("[+] Changed to:", new_mac_address)
        # Disable and then re-enable the adapter to apply changes
        disable_adapter(adapter_index)
        print("[+] Adapter is disabled (；￣Д￣)")
        enable_adapter(adapter_index)
        print("[+] Adapter is enabled again ☆ ～('▽^人)")

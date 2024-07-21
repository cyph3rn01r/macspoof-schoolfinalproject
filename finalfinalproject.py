import subprocess
import re
import string
import random

# the registry path of network interfaces
network_interface_reg_path = r"HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\Class\\{4d36e972-e325-11ce-bfc1-08002be10318}"
# the transport name regular expression, looks like {AF1B45DB-B5D4-46D0-B4EA-3E18FA49BF5F}
transport_name_regex = re.compile(r"{.+}")
# the MAC address regular expression
mac_address_regex = re.compile(r"([A-F0-9]{2}[:-]){5}([A-F0-9]{2})")

def get_random_mac_address():
    """Generate and return a MAC address in the format of WINDOWS"""
    uppercased_hexdigits = ''.join(set(string.hexdigits.upper()))
    return random.choice(uppercased_hexdigits) + random.choice("24AE") + ":" + ":".join("".join(random.sample(uppercased_hexdigits, k=2)) for _ in range(5))

def clean_mac(mac):
    """Simple function to clean non hexadecimal characters from a MAC address
    mostly used to remove '-' and ':' from MAC addresses and also uppercase it"""
    return "".join(c for c in mac if c in string.hexdigits).upper()

def get_connected_adapters_mac_address():
    connected_adapters_mac = []
    try:
        for potential_mac in subprocess.check_output("getmac").decode().splitlines():
            mac_address = mac_address_regex.search(potential_mac)
            transport_name = transport_name_regex.search(potential_mac)
            if mac_address and transport_name:
                connected_adapters_mac.append((mac_address.group(), transport_name.group()))
    except subprocess.CalledProcessError as e:
        print(f"Failed to get connected adapters: {e}")
    return connected_adapters_mac

def change_mac_address(adapter_transport_name, new_mac_address):
    try:
        output = subprocess.check_output(f"reg QUERY " +  network_interface_reg_path.replace("\\\\", "\\")).decode()
        for interface in re.findall(rf"{network_interface_reg_path}\\\d+", output):
            adapter_index = int(interface.split("\\")[-1])
            interface_content = subprocess.check_output(f"reg QUERY {interface.strip()}").decode()
            if adapter_transport_name in interface_content:
                changing_mac_output = subprocess.check_output(f"reg add {interface} /v NetworkAddress /d {new_mac_address} /f").decode()
                print(changing_mac_output)
                break
        return adapter_index
    except subprocess.CalledProcessError as e:
        print(f"Failed to change MAC address: {e}")
        return None

def disable_adapter(adapter_index):
    try:
        disable_output = subprocess.check_output(f"wmic path win32_networkadapter where index={adapter_index} call disable").decode()
        return disable_output
    except subprocess.CalledProcessError as e:
        print(f"Failed to disable adapter: {e}")
        return None

def enable_adapter(adapter_index):
    try:
        enable_output = subprocess.check_output(f"wmic path win32_networkadapter where index={adapter_index} call enable").decode()
        return enable_output
    except subprocess.CalledProcessError as e:
        print(f"Failed to enable adapter: {e}")
        return None

def get_user_adapter_choice(connected_adapters_mac):
    print("Available adapters:")
    for i, (mac, transport_name) in enumerate(connected_adapters_mac, 1):
        print(f"{i}. MAC: {mac}, Transport Name: {transport_name}")
    choice = int(input("Select adapter to change (1-{}): ".format(len(connected_adapters_mac))))
    return connected_adapters_mac[choice - 1]

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Python Windows MAC changer")
    parser.add_argument("-r", "--random", action="store_true", help="Whether to generate a random MAC address")
    parser.add_argument("-m", "--mac", help="The new MAC you want to change to")
    args = parser.parse_args()

    if args.random:
        new_mac_address = get_random_mac_address()
    elif args.mac:
        new_mac_address = clean_mac(args.mac)

    connected_adapters_mac = get_connected_adapters_mac_address()
    old_mac_address, target_transport_name = get_user_adapter_choice(connected_adapters_mac)
    print("[*] Old MAC address:", old_mac_address)
    adapter_index = change_mac_address(target_transport_name, new_mac_address)
    if adapter_index is not None:
        print("[+] Changed to:", new_mac_address)
        disable_adapter(adapter_index)
        print("[+] Adapter is disabled")
        enable_adapter(adapter_index)
        print("[+] Adapter is enabled again")

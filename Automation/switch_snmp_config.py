import yaml
from datetime import datetime
from netmiko import ConnectHandler
from netmiko.exceptions import NetMikoTimeoutException, NetMikoAuthenticationException

# Load the unified inventory file
with open("inventory.yml", "r") as f:
    inventory_data = yaml.safe_load(f)

log_filename = f"automation_switches_snmp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

with open(log_filename, "w") as log:
    # Iterate ONLY over the switches
    for device in inventory_data.get("switches", []):
        hostname = device.pop("hostname", "Unknown")
        config_filename = device.pop("config_file", None)
        
        log.write(f"\n[{datetime.now()}] Connecting to {hostname} ({device['host']})...\n")
        print(f"Connecting to {hostname} to push SNMP...")

        try:
            with open(config_filename, "r") as f:
                cmds = yaml.safe_load(f)
        except Exception as e:
            print(f"ERROR reading {config_filename}: {str(e)}")
            continue

        try:
            net_connect = ConnectHandler(**device)
            net_connect.enable()
            output = net_connect.send_config_set(cmds)
            log.write(output)
            log.write(f"\n[{datetime.now()}] SUCCESS: SNMP Configured on {hostname}\n")
            print(f"SUCCESS: {hostname} SNMP configured successfully.")
            net_connect.disconnect()
        except Exception as e:
            err_msg = f"ERROR on {hostname}: {str(e)}"
            log.write(err_msg + "\n")
            print(err_msg)

print(f"\nSwitch SNMP automation complete. Logs written to {log_filename}")

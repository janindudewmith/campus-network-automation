import yaml
from netmiko import ConnectHandler

# Load your existing inventory
with open("inventory.yml", "r") as f:
    data = yaml.safe_load(f)

commands_to_check = [
    "show ip interface brief",
    "show ip ospf neighbor"
]

for router in data["routers"]:
    hostname = router.pop("hostname", "Unknown")
    print(f"\n{'='*40}\nChecking {hostname}...\n{'='*40}")

    try:
        net_connect = ConnectHandler(**router)
        net_connect.enable()

        for cmd in commands_to_check:
            print(f"\n--- Output for '{cmd}' ---")
            print(net_connect.send_command(cmd))

        net_connect.disconnect()
    except Exception as e:
        print(f"Failed to connect to {hostname}: {str(e)}")

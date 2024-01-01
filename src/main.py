import subprocess
import time
import schedule
from datetime import datetime, timedelta

def generate_hostapd_conf(config):
    conf_content = "\n".join([f"{key}={value}" for key, value in config.items()])
    with open('/etc/hostapd/hostapd.conf', 'w') as conf_file:
        conf_file.write(conf_content)

def generate_allowed_macs_file(config):
    allowed_macs_content = "22:52:fb:b4:e0:d9 08:00-16:00\nd0:49:7c:3b:ac:0a 12:00-22:00"
    with open(config['accept_mac_file'], 'w') as allowed_macs_file:
        allowed_macs_file.write(allowed_macs_content)


# Function to disconnect users based on the time
def disconnect_users():
    with open(wifi_config['accept_mac_file']) as f:
        for line in f:
            mac, allowed_time = line.strip().split()
            current_time = datetime.now().strftime('%H:%M')
            
            if current_time > allowed_time:
                deauthenticate_command = f"hostapd_cli deauthenticate {mac}"
                subprocess.run(deauthenticate_command, shell=True)

if __name__=='__main__':

    #Wi-Fi configuration
    wifi_config = {
        'interface': 'wlo1',
        'driver': 'nl80211',
        'ssid': 'El_meu_AP',
        'hw_mode': 'g',
        'channel': 6,
        'wmm_enabled': 0,
        'macaddr_acl': 1,
        'accept_mac_file': '/etc/hostapd/allowed_macs.txt',
        }
    
    # Generate hostapd.conf and allowed_macs.txt files
    generate_hostapd_conf(wifi_config)
    generate_allowed_macs_file(wifi_config)

    # Schedule the disconnect function every 5 minutes
    schedule.every(5).minutes.do(disconnect_users)

    # Start hostapd
    start_command = f"hostapd -B /etc/hostapd/hostapd.conf"
    subprocess.run(start_command, shell=True)

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")

    # Stop hostapd on exit
    stop_command = "pkill hostapd"
    subprocess.run(stop_command, shell=True)

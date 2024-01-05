import subprocess
import time
import schedule
from datetime import datetime, timedelta
import re
import smtplib
import threading

scheduler_running = True

#Connected MAC list
connected_macs=[]

#Function to generate hostapd configuration file
def generate_hostapd_conf(config):
    conf_content = "\n".join([f"{key}={value}" for key, value in config.items()])
    with open('hostapd.conf', 'w') as conf_file:
        conf_file.write(conf_content)

# Function to disconnect users based on the time
def update_accept_MAC_list():
    lines_to_keep = []
    accepted_macs=[]
    try:
        with open('allowed_macs.txt') as f:
            for line in f:
                accepted_macs.append(line.strip())
    except:
        pass
    try:
        with open('time_ranges.txt') as f:
            for line in f:
                mac, initial_time, final_time = line.strip().split()
                current_time = datetime.now().strftime('%H:%M')
                if current_time >= initial_time and current_time < final_time:
                    lines_to_keep.append(mac)
                    if mac not in accepted_macs:
                        subprocess.run(f"hostapd_cli accept_acl ADD_MAC {mac}", shell=True)
                else:
                    if mac in accepted_macs:
                        subprocess.run(f"hostapd_cli accept_acl DEL_MAC {mac}", shell=True)
                        if mac in connected_macs:
                            print(mac, "reached end time.")
        with open('allowed_macs.txt', 'w') as f:
            f.writelines(lines_to_keep)
    except:
        pass
    

def validate_mac_address(mac_address):
    # Validate MAC address format
    mac_pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
    return bool(mac_pattern.match(mac_address))

def validate_time_format(time_str):
    # Validate time format (HH:MM)
    time_pattern = re.compile(r'^([01]\d|2[0-3]):([0-5]\d)$')
    return bool(time_pattern.match(time_str))

def generate_allowed_macs_file():
    # Get MAC address from the user and validate the format
    mac_address = input("Enter MAC address: ").strip()
    while not validate_mac_address(mac_address):
        print("Invalid MAC address format.")
        mac_address = input("Enter MAC address: ").strip()

    # Get initial time from the user and validate the format
    initial_time = input("Enter initial time (HH:MM): ").strip()
    while not validate_time_format(initial_time):
        print("Invalid time format. Please use HH:MM format.")
        initial_time = input("Enter initial time (HH:MM): ").strip()

    # Get final time from the user and validate the format and order
    final_time = input("Enter final time (HH:MM): ").strip()
    while (not validate_time_format(final_time)) or final_time < initial_time:
        print("Invalid time format or order. Final time should be greater than initial time.")
        final_time = input("Enter final time (HH:MM): ").strip()

    # Save data to files
    with open('time_ranges.txt', 'a') as time_file:
        time_file.write(f"{mac_address} {initial_time} {final_time}\n")


def parse_mac_address(log_entry):
    match = re.search(r"([0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2})", log_entry)
    return match.group(1) if match else None

def update_mac_lists(log_entry):
    global connected_macs
    mac_address = parse_mac_address(log_entry)
    if "AP-STA-CONNECTED" in log_entry and mac_address:
        connected_macs.append(mac_address)
        print(mac_address, "connected")
    elif "AP-STA-DISCONNECTED" in log_entry and mac_address:
        connected_macs = [mac for mac in connected_macs if mac != mac_address]
        print(mac_address, "disconnected")

def monitor_log_file():
    with open('log_file.log', 'r+') as log_file:
        output = log_file.read()
        log_file.truncate(0)
    for log_entry in output.splitlines():
        update_mac_lists(log_entry)


def validate_email(email):
    # Basic email format validation
    pattern = re.compile(r"[^@]+@[^@]+\.[^@]+")
    return re.match(pattern, email)

def send_email(correu, assumpte, text):
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login("proves908767@gmail.com", "lpxwyfipjftgfcnr")
        message = f'Subject: {assumpte}\n\n{text}'
        server.sendmail("proves908767@gmail.com", correu, message)
        server.close()
    except Exception as e:
        pass        

#We create the following thread so that scheduled jobs are executed at the right time while we have the menu working
def background_scheduler():
    global scheduler_running
    while scheduler_running:
        schedule.run_pending()
        time.sleep(1)

scheduler_thread = threading.Thread(target=background_scheduler)

def main():
    admin_email = ""
    max_attempts = 3
    attempts = 0
    #Wi-Fi configuration
    wifi_config = {
        'interface': 'wlp3s0',
        'driver': 'nl80211',
        'ssid': 'HotspotAbelJoel',
        'hw_mode': 'g',
        'channel': 9,
        'ctrl_interface': '/var/run/hostapd',
        'macaddr_acl': 1,
    }

    # Generate hostapd.conf file
    generate_hostapd_conf(wifi_config)

    # Request administrator's email
    while attempts < max_attempts:
        admin_email = input("Enter the admin email address: ")

        if validate_email(admin_email):
            break
        else:
            attempts += 1
            print(f"Incorrect email format. Attempt {attempts} of {max_attempts}.\n")

    if attempts == max_attempts:
        print("Too many failed attempts. Exiting the program.")
        return
    
    # Generate hostapd.conf file
    generate_hostapd_conf(wifi_config)

    # Schedule the disconnect function every 1 minute
    schedule.every(10).seconds.do(update_accept_MAC_list)

    # Schedule the monitoring function
    schedule.every(20).seconds.do(monitor_log_file)

    # Start hostapd
    start_command = f"hostapd hostapd.conf > log_file.log 2>&1 &"
    subprocess.run(start_command, shell=True)

    time.sleep(1)

    update_accept_MAC_list()

    scheduler_thread.start()

    try:
        while True:
            print('#' * 20)
            print("MENU".center(20, ' '))
            print('#' * 20)
            print("1. Enter accepted MAC list for your AP")
            print("2. Show the list of devices of interest and the time interval when they can connect")
            print("3. Devices connected at this time")
            print("4. Receive information from the third and fourth option via email")
            print("5. Exit")

            choice = input("Select an option (1-5): ")

            if choice == '1':
                print("Option 1 selected.")
                while True:
                    generate_allowed_macs_file()
                    another_entry = input("Do you want to add a new MAC address to the accept list? (Y/N): ").strip().upper()
                    while another_entry != 'Y' and another_entry != 'N':
                        print("Invalid input. Please enter 'Y' or 'N'.")
                        another_entry = input("Do you want to add a new MAC address to the accept list? (Y/N): ").strip().upper()
                    if another_entry == 'N':
                        print("Data saved successfully.")
                        print("Initializing your AP.")
                        break
            elif choice == '2':
                # Logic for the second option
                print("Option 2 selected.")
            elif choice == '3':
                # Logic for the third option
                print("Option 3 selected.")
            elif choice == '4':
                # Logic for the fourth option
                print("Option 4 selected.")
                subject = "Information about connected devices"
                body = "Here is the information you want to send via email."
                send_email(admin_email, subject, body)
                print(f"Information sent by email to {admin_email}.")
            elif choice == '5':
                print("Exiting the program. Goodbye!")
                break
            else:
                print("Invalid option. Please select an option from 1 to 5.")
    except:
        print("Exiting...")
    
    # Stop hostapd on exit
    stop_command = "pkill hostapd"
    subprocess.run(stop_command, shell=True)
    return

    


if __name__=='__main__':
    main()



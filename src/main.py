import subprocess
import time
import schedule
from datetime import datetime, timedelta
import re
import smtplib
import threading
from tabulate import tabulate
from email.mime.text import MIMEText
import sys


connected_macs=[] #Connected MAC list
first_iteration=True
scheduler_running = True
MAX_ATTEMPTS = 3 # maximum number of times you can enter the email
#Wi-Fi configuration
WIFI_CONFIG = {
    'interface': 'wlp3s0',
    'driver': 'nl80211',
    'ssid': 'HotspotAbelJoel',
    'hw_mode': 'g',
    'channel': 9,
    'ctrl_interface' : '/var/run/hostapd',
    'macaddr_acl': 1,
}

    
def validate_mac_address(mac_address):
    """
    This function validates the format of the MAC address returning true if it is right and false if it is wrong.
    :param mac_address: Mac address
    :type mac_address: str
    """
    mac_pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
    return bool(mac_pattern.match(mac_address))

def validate_time_format(time_str):
    """
    This function validates the format of the time range during which the device can be connected to the access point (AP), returning true if it is correct and false if it is incorrect.
    :param time_str: time
    :type time_str: str
    """
    # Validate time format (HH:MM)
    time_pattern = re.compile(r'^([01]\d|2[0-3]):([0-5]\d)$')
    return bool(time_pattern.match(time_str))

def validate_email(email):
    """
    This function validates the format of the MAC address returning true if it is right and false if it is wrong.
    :param email: email
    :type email: str
    """
    pattern = re.compile(r"[^@]+@[^@]+\.[^@]+")
    return re.match(pattern, email)

def parse_mac_address(log_entry):
    match = re.search(r"([0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2})", log_entry)
    return match.group(1) if match else None


def generate_hostapd_conf(config):
    """
    Function to generate hostapd configuration file.
    """
    conf_content = "\n".join([f"{key}={value}" for key, value in config.items()])
    with open('hostapd.conf', 'w') as conf_file:
        conf_file.write(conf_content)

def update_accept_MAC_list():
    """
    Function designed to update the list of devices that can connect to the AP.
    """
    global first_iteration
    lines_to_keep = []
    accepted_macs=[]
    try:
        if not first_iteration:
            with open('allowed_macs.txt') as f:
                for line in f:
                    accepted_macs.append(line.strip())
        else:
            first_iteration=False
    except FileNotFoundError:
        pass
    try:
        with open('time_ranges.txt') as f:
            for line in f:
                mac, initial_time, final_time = line.strip().split()
                current_time = datetime.now().strftime('%H:%M')
                if current_time >= initial_time and current_time < final_time:
                    lines_to_keep.append(mac)
                    if mac not in accepted_macs:
                        subprocess.run(f"hostapd_cli accept_acl ADD_MAC {mac} > /dev/null", shell=True)
                else:
                    if mac in accepted_macs:
                        subprocess.run(f"hostapd_cli accept_acl DEL_MAC {mac} > /dev/null", shell=True)
        with open('allowed_macs.txt', 'w') as f:
            f.writelines(lines_to_keep)
    except FileNotFoundError:
        pass


def update_allowed_devices_list():
    """
    Function designed to update the list of devices that can connect to the access point (AP). It allows adding as many MAC addresses as desired with the associated time range, saving them to the file time_ranges.txt.
    """
    mac_address = input("Enter MAC address: ").strip()
    while not validate_mac_address(mac_address):
        print("Invalid MAC address format.")
        mac_address = input("Enter MAC address: ").strip()

    initial_time = input("Enter initial time (HH:MM): ").strip()
    while not validate_time_format(initial_time):
        print("Invalid time format. Please use HH:MM format.")
        initial_time = input("Enter initial time (HH:MM): ").strip()

    final_time = input("Enter final time (HH:MM): ").strip()
    while (not validate_time_format(final_time)) or final_time < initial_time:
        print("Invalid time format or order. Final time should be greater than initial time.")
        final_time = input("Enter final time (HH:MM): ").strip()

    with open('time_ranges.txt', 'a') as time_file:
        time_file.write(f"{mac_address} {initial_time} {final_time}\n")


def monitor_device_connection(log_entry):
    """
    Function created to determine whether a device has connected or disconnected from the access point (AP). When a device connects or disconnects, an email is sent to the master's email address indicating the MAC address of the device that has connected or disconnected.
    """
    global connected_macs
    mac_address = parse_mac_address(log_entry)
    if "AP-STA-CONNECTED" in log_entry and mac_address:
        connected_macs.append(mac_address)
        subject = f"Device connected from AP: {mac_address}"
        body = f"The device with MAC {mac_address} has connected from the AP."
        send_email(admin_email, subject, body)
    elif "AP-STA-DISCONNECTED" in log_entry and mac_address:
        with open('time_ranges.txt', 'r') as file:
            lines = file.readlines()
            for line in lines:
                mac, start, end = line.strip().split()
                if mac == mac_address:
                    if start <= datetime.now().strftime('%H:%M') <= end:
                        # The device was disconnected for another reason
                        connected_macs = [mac for mac in connected_macs if mac != mac_address]
                        subject = f"Device disconnected from AP: {mac_address}"
                        body = f"The device with MAC {mac_address} has disconnected from the AP for an unknown reason."
                        send_email(admin_email, subject, body)
                    else:
                        # The device was disconnected because access timed out
                        connected_macs = [mac for mac in connected_macs if mac != mac_address]
                        subject = f"Device disconnected from AP: {mac_address}"
                        body = f"The device with MAC {mac_address} has disconnected from the AP because the access time has expired (from {start} to {end})."
                        send_email(admin_email, subject, body)
                    break  

def monitor_log_file():
    """
    Function used to read the content generated by hostapd in order to monitor the connection of devices.
    """
    with open('log_file.log', 'r+') as log_file:
        output = log_file.read()
        log_file.truncate(0)
    for log_entry in output.splitlines():
        monitor_device_connection(log_entry)


def send_email(email, subject, text):
    """
    Function created to send emails to the administrator of the AP in order to keep them informed of the activity.

    :param email: The email address to which the email will be sent.
    :type email: str
    :param subject: The subject of the email.
    :type subject: str
    :param text: The body/content of the email in HTML format.
    :type text: str
    """
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login("proves908767@gmail.com", "lpxwyfipjftgfcnr")
        message = f'Subject: {subject}\nMIME-Version: 1.0\nContent-type: text/html\n\n{text}'
        server.sendmail("proves908767@gmail.com", email, message)
        server.close()
    except Exception as e:
        pass        

def generate_table(data, headers, send_email=False):
    """
    Generate a table in HTML format for email or using tabulate for terminal.

    :param data: List of data rows.
    :type data: list
    :param headers: List of table headers.
    :type headers: list
    :param send_email: Indicates whether the table should be generated for email (True) or terminal (False).
    :type send_email: bool
    """
    try:
        if send_email:
            table = "<table style='border-collapse: collapse; width: 100%; border: 1px solid black;' cellpadding='5'><thead><tr>"
            table += ''.join(f"<th style='border: 1px solid black; padding: 8px;'>{header}</th>" for header in headers)
            table += "</tr></thead><tbody>"

            for row in data:
                table += "<tr>"
                table += ''.join(f"<td style='border: 1px solid black; padding: 8px;'>{cell}</td>" for cell in row)
                table += "</tr>"

            table += "</tbody></table>"
            return table
        else:
            return tabulate(data, headers, tablefmt="fancy_grid")
    except Exception as e:
        return f"Error: {str(e)}"


def display_device_info(send_email=False):
    """
    Generate a table or report of devices of interest for the AP.

    :param send_email: Indicates whether the table should be generated for email (True) or terminal (False).
    :type send_email: bool
    """
    headers = ["MAC DEVICE", "Initial Time Access", "Final Time Access"]
    table_data = []

    try:
        with open("time_ranges.txt", 'r') as file:
            lines = file.readlines()
            for line in lines:
                mac, start_time, end_time = line.strip().split()
                table_data.append([mac, start_time, end_time])

        if not table_data:
            return "There are no associated devices in the list of interest."

        return generate_table(table_data, headers, send_email)
    except FileNotFoundError:
        return "There are no associated devices in the list of interest."
    except Exception as e:
        return f"Error: {str(e)}"


def display_device_connected(connected_macs, send_email=False):
    """
    Generate a table or report of connected devices for the AP.

    :param connected_macs: List of MAC addresses of connected devices.
    :type connected_macs: list
    :param send_email: Indicates whether the table should be generated for email (True) or terminal (False).
    :type send_email: bool
    """
    headers = ["MAC DEVICE"]

    if not connected_macs:
        return "There are no connected devices in the AP."

    try:
        new_list = [[mac] for mac in connected_macs]
        return generate_table(new_list, headers, send_email)
    except Exception as e:
        return f"Error: {str(e)}"


def background_scheduler():
    """
    We create the following thread so that scheduled jobs are executed at the right time while we have the menu working.
    """
    global scheduler_running
    while scheduler_running:
        schedule.run_pending()
        time.sleep(1)


def main():
    """
    The main function orchestrates the usage of previously created functions.
    It sets up the hostapd and initializes two subprocesses to monitor device connections
    and disconnections, as well as control their usage based on time ranges to either
    disconnect them from the AP or grant permission for connection. Additionally, it provides
    a menu with a set of instructions that can be very useful for the administrator.
    """
    global scheduler_running
    global admin_email
    max_attempts = 3
    attempts = 0
    try:
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
    except KeyboardInterrupt:
        print("\nExiting the program by user interrupt (Ctrl+C). Goodbye!")
        sys.exit(0)

    try:
        generate_hostapd_conf(WIFI_CONFIG)
        # Schedule the update_accept_MAC_list function every 10 seconds
        schedule.every(10).seconds.do(update_accept_MAC_list)
        # Schedule the monitoring function
        schedule.every(20).seconds.do(monitor_log_file)
        # Start hostapd
        start_command = f"hostapd hostapd.conf > log_file.log 2>&1 &"
        subprocess.run(start_command, shell=True)
        time.sleep(1)
        update_accept_MAC_list()
        scheduler_thread = threading.Thread(target=background_scheduler)
        scheduler_thread.start()

        while True:
            print('#' * 20)
            print("MENU".center(20, ' '))
            print('#' * 20)
            print("1. Enter accepted MAC list for your AP")
            print("2. Show the list of devices of interest and the time interval when they can connect")
            print("3. Devices connected at this time")
            print("4. Receive information from the second and third option via email")
            print("5. Exit")

            choice = input("Select an option (1-5): ")

            if choice == '1':
                print("Option 1 selected.")
                while True:
                    update_allowed_devices_list()
                    another_entry = input("Do you want to add a new MAC address to the accept list? (Y/N): ").strip().upper()
                    while another_entry != 'Y' and another_entry != 'N':
                        print("Invalid input. Please enter 'Y' or 'N'.")
                        another_entry = input("Do you want to add a new MAC address to the accept list? (Y/N): ").strip().upper()
                    if another_entry == 'N':
                        print("Data saved successfully.")
                        print("Initializing your AP.")
                        break
            elif choice == '2':
                print("Option 2 selected.")
                print(display_device_info(False))
            elif choice == '3':
                print("Option 3 selected.")
                print(display_device_connected(False))
            elif choice == '4':
                print("Option 4 selected.")
                subject = "Information about connected devices and of interest"
                body = f"<p>Table: Information about interest devices</p>{display_device_info(True)}"
                body += f"<p>Table: Connected Devices</p>{display_device_connected(connected_macs, True)}"
                send_email(admin_email, subject, body)
                print(f"Information sent by email to {admin_email}.")
            elif choice == '5':
                print("Exiting the program. Goodbye!")
                scheduler_running=False
                scheduler_thread.join()
                stop_command = "pkill hostapd"
                subprocess.run(stop_command, shell=True)
                sys.exit(0)
            else:
                print("Invalid option. Please select an option from 1 to 5.")
    except KeyboardInterrupt:
        print("Exiting the program. Goodbye!")
        # Stop hostapd on exit
        scheduler_running=False
        scheduler_thread.join()
        stop_command = "pkill hostapd"
        subprocess.run(stop_command, shell=True)
        sys.exit(0)


if __name__=='__main__':
    main()

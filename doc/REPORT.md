# Report
The main objective of this file is to explain:

1. The functionalities implemented for the program, as well as the design chosen for each one.
2. The resulting menu that allows to control all the system.

## Designs and implementations
This section is divided into different subsections, each of them corresponding to a main functionality implemented for the AP program.

### Main program
First of all, it is important to understand the main functionality of the program [src/main.py](../src/main.py). The aim of this program is to create the corresponding AP by using hostapd tools. It also gives the user an interface (by a simple menu) to control the functionalities of the program: 

- Sending information by email.
- Controlling the accepted MAC list and the corresponding periods of time for each MAC.
- Showing the important information in the same menu.

As there must be parallel processes running at the same time, in this project we use both threads and subprocesses. 

Thus, the design implemented for the `main()` function is the following:

1. Asks for an admin email where it must send all the important information. Validates the email using the function `validate_email()`.
2. Generates the corresponding hostapd configuration file using the function ` generate_hostapd_conf(WIFI_CONFIG)`. `WIFI_CONFIG` is a dictionary with the configuration parameters wanted in the hostapd configuration file.
3. By using the `schedule` Python library, schedules the function `update_accept_MAC_list()` each 10 seconds.
4. By using the `schedule` Python library, schedules the function `monitor_log_file()` each 20 seconds.
5. By using the `subprocess` Python library, runs a subprocess for the hostapd AP with its corresponding configuration file. It also redirects stdout and stderr of this subprocess to a file called `log_file.log`.
6. By using the `threading` Python library, creates a thread that executes the `background_scheduler()` function.
7. Enters to an infinite loop where it shows the control menu and expects for an option selection from the user. The options that can be executed with this menu are the following:
- Option 1: Asks for a MAC and its corresponding accepted period of time. Updates the allowed MAC list by calling the function `update_allowed_devices_list()`. Repeats this process till the user is finished.
- Option 2: Shows the list of devices of interest and the time interval when they can connect by calling the function `display_device_info()`.
- Option 3: Shows the list of devices connected at this time by calling the function `display_device_connected()`.
- Option 4: Sends an email to the admin mail. On the one hand, this mail shows a table with the devices of interest and the time interval when they can connect. On the other hand, it shows a table with the connected deviced in that moment. It uses the function `send_email()` to send the email properly formating the data in tables.
- Option 5: Exits the program. This requires killing all the child processes and the threads previously created.
8. Additionally, if Keyboard Interrupt, the program also exits, killing all the child processes and the threads previously created.

Each of the mentioned functions are explained in the following subsections.

### Validation functions

The functions `validate_email()`, `validate_mac_address()`, `validate_time_format()` and `parse_mac_address()` are all validation functions. This means that their main objective is to return a bool that indicates if the entered string fullfils the data format requirments. In our case, they are used to validate that the data entered by the user is correct, showing error messages in case it is not, and expecting new inputs in those cases.

### Function `generate_hostapd_conf()`

This function generates the file hostapd.conf that will be used by the hostapd AP. The parameters of the configuration are given by dictionary. This dictionary is initally defined in the program and can be modified if different or new parameters are needed.

### Function `update_accept_MAC_list()`

This function is executed each 10 seconds. The design implemented for this function is the following:

1. Opens the file `allowed_macs.txt`, which is the one that saves the white list for the MAC's that were allowed in the previous data update. Reads this file, and saves the MAC's in a list `accepted_macs`.
2. Opens the file `time_ranges.txt`, which is the one that saves the devices of interest's MAC and the allowed period of time for each one. Reads this file line by line. For each line, checks if the current time is between the period of time of the MAC: 
- If it is, it adds this MAC to a list `lines_to_keep`. If this mac is not in `accepted_macs` list, runs a subprocess that executes the command line for adding this mac in the white list of the hostapd.
- If it is not and mac is in `accepted_macs` list, runs a subprocess that executes the command line for deleting this mac from the white list of the hostapd.
3. Opens again the file `allowed_macs.txt` and updates it by writing only the MAC's saved in the list `lines_to_keep`. 

This way, only MAC's allowed in the current time are saved.

### Function `monitor_log_file()`

This function is executed each 20 seconds. The design implemented for this function is the following:

1. Opens the file `log_file.log`. Reads all the content, saves it in a variable, and deletes all the content in the file. Remember that this file saves the stdout and stderr of the hostapd subprocess.
2. For each line of the file, executes the function `monitor_device_connection(line)`.

The design implemented for `monitor_device_connection(line)` is the following:

1. If the log file line corresponds to a connection type (contains the substring "AP-STA-CONNECTED"), it adds the MAC to a global variable list called `connected_macs`. It also sends an email using the function `send_email()` in order to notify the admin about the MAC connection.

2. If the log file line corresponds to a disconnection type (contains the substring "AP-STA-DISCONNECTED"), it deletes the MAC from the global variable list called `connected_macs`. Then, by opening the file `time_ranges.txt`, it checks if the corresponding MAC reached end time.
- If it did, it sends an email notifying the admin that this MAC disconnected due to time expiration.
- If it did not, it sends an email notifying the admin that this MAC disconnected.
In both cases, it uses again the function `send_email()` for sending the corresponding email.


### Function `background_scheduler()`

Using Python library `scheduler`, this function (executed by a thread) constantly checks if it should execute any pending function. Remember that `update_accept_MAC_list()` is scheduled every 10 seconds, and `monitor_log_file()` every 20 seconds.


### Function `update_allowed_devices_list()`

This function asks for a MAC and its corresponding accepted period of time. Then opens the file called `time_ranges.txt` and writes a line for each MAC. In each line the program writes the corrsponding MAC, the initial time and the end time, all separated by a space.


### Function `display_device_info()`

This function generates a table or report of devices of interest for the AP. The design implemented for this function is the following:

1. Opens the file `time_ranges.txt`.
2. For each line of the file, saves the data in a local list of the function called `table_data`.
3. Returns the call to the function `generate_table()` with `table_data` as a parameter. This function generates a table in HTML format for email or using tabulate for terminal.


### Function `display_device_connected()`

This function generates a table or report of connected devices for the AP. The design implemented for this function is the following:

1. Checks the content of the global variable called `connected_macs`.
2. Returns the call to the function `generate_table()` with `connected_macs` content as a parameter. This function generates a table in HTML format for email or using tabulate for terminal.

### Function `send_email()`

This function sends emails to the administrator of the AP in order to keep them informed of the activity. The implementation in this case uses Python library `smtplib`. This function should be called with the corresponding receiver email, subject and body as parameters.

## Results

In this section, the results of the project are presented.

### The control menu

Once executed the main program, the first procedure is the admin email input. Below it is shown:
![Captura desde 2024-01-06 19-21-39](https://github.com/AbEl9876/hostapd/assets/133850497/072488e7-df33-4205-81db-70aaae153e54)

Then, the AP is in initialized and the control menu is shown:


- If option 1 is chosen, new accepted MAC's with their corresponding periods of time can be entered. Below an example of this option:

![Captura desde 2024-01-06 19-23-04](https://github.com/AbEl9876/hostapd/assets/133850497/a0033ccc-87a7-4ac8-b3ea-0164bf21b14b)

- If option 2 is chosen, a list of devices of interest and the time interval when they can connect is shown. Below an example of this option:

![Captura desde 2024-01-06 19-26-13](https://github.com/AbEl9876/hostapd/assets/133850497/dd3dab62-2207-4363-9035-3c1ef40ab365)

- If option 3 is chosen, a list of connected devices to the AP is shown. Below an example of this option:

![Captura desde 2024-01-06 19-32-08](https://github.com/AbEl9876/hostapd/assets/133850497/220cf22c-fa6c-4b7f-b173-6d1db6ef0104)

- If option 4 is chosen, the information given for option 2 and 3 (devices of interest, and connected devices) is sent by email to the admin email entered at the beginning of the program. The resulting email is shown in the next subsection.


### Notifications

We have four types of notification implemented for our program:

1. **Email Connection:**

![Captura desde 2024-01-06 19-50-53](https://github.com/AbEl9876/hostapd/assets/133850497/59a93d92-a486-4937-8225-e5e5de7b7e1e)

2. **Email Disconnection due to end time:**

![Captura desde 2024-01-06 19-53-14](https://github.com/AbEl9876/hostapd/assets/133850497/53c87576-a1d7-4a22-aeae-ce11dd15683a)

3. **Email Normal disconnection:**

![Captura desde 2024-01-06 19-50-14](https://github.com/AbEl9876/hostapd/assets/133850497/8537f055-8339-4b78-a37e-54ebb68ea582)

4. **Email sent by choosing the Option 4 in the menu. This mail shows the devices of interest and also the connected devices:**

![Captura desde 2024-01-06 19-51-47](https://github.com/AbEl9876/hostapd/assets/133850497/f87ece2b-d7ea-4b93-8363-706deaf4f123)

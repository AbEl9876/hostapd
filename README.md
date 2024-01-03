# Wi-Fi Access Point with Time-Based Access Control

This project aims to create a Wi-Fi Access Point (AP) featuring time-based access control, allowing or restricting network access based on specific MAC addresses and time constraints.

### Prerequisites

To set up this project, you'll need:

- A computer running a Linux operating system.
- Python 3 installed on the system.
- Required packages: `dnsmasq` and `hostapd`.
- Two Network Interfaces: One wireless (Wi-Fi) interface and one Ethernet interface.

### Network Interface Purpose

The Wi-Fi interface is dedicated to functioning as the Access Point (AP), managing network connections and enforcing access control based on specified rules.

The Ethernet interface serves the purpose of providing internet connectivity to the device responsible for creating the AP. It allows the AP to share the internet connection with devices connecting to it.

### Key Features

The project encompasses essential functionalities, including:

1. **Time-Based Access Control:**
   - Regulate network access based on predefined time intervals for specific MAC addresses.

2. **Monitoring:**
   - Notification system alerts the administrator when specified "devices of interest" connect to the network via their MAC addresses.
   - Customizable management of the list of monitored devices.
   - Flexible notification methods tailored to the administrator's preferences.

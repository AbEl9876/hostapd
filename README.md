# Wi-Fi Access Point with Time-Based Access Control

This project aims to create a Wi-Fi Access Point (AP) featuring time-based access control, allowing or restricting network access based on specific MAC addresses and time constraints.

### Key Features

The project encompasses essential functionalities, including:

1. **Time-Based Access Control:**
   - Regulate network access based on predefined time intervals for specific MAC addresses.

2. **Monitoring:**
   - Notification system alerts the administrator when specified "devices of interest" connect to the network via their MAC addresses.
   - Customizable management of the list of monitored devices.
   - Flexible notification methods tailored to the administrator's preferences.

### Prerequisites

To set up this project, you'll need:

- A computer running a Linux operating system.
- Python 3 installed on the system.
- Required packages: `dnsmasq` and `hostapd`.
- Two Network Interfaces: One wireless (Wi-Fi) interface and one Ethernet interface.

### Network Interface Purpose

The Wi-Fi interface is dedicated to functioning as the Access Point (AP), managing network connections and enforcing access control based on specified rules.

The Ethernet interface serves the purpose of providing internet connectivity to the device responsible for creating the AP. It allows the AP to share the internet connection with devices connecting to it.

In our case, the Wi-Fi interface is named wlp3s0 and the Ethernet is named enp4s0. Remember, in the following steps to create the Access Point (AP), adapt the interface names to those of your computer. 

## Steps to Create the Access Point (AP)

This section provides a guide on how to create the Access Point (AP) and initiate the console.

### Setup Guide

#### **Step 1: Setting up Interface IP Address** 
We modify the `/etc/network/interfaces` file (sudo nano /etc/network/interfaces) to configure the Wi-Fi interface (it will act as our AP) with a static IP address within a private network.
```bash
auto wlp3s0
iface wlp3s0 inet static
address 172.16.0.1
netmask 255.255.255.0
```

#### **Step 2: Configuring DHCP Server** 
We use dnsmasq to provide DHCP services, assigning IP addresses to devices that connect to the AP. The dnsmasq service uses port 53 just like the `systemd-resolved` service. Therefore we have to free port 53:
```bash
sudo systemctl stop systemd-resolved
```

Before we start creating all the configuration files, let's create the folder where all the necessary files for setting up the AP will be located.
```bash
mkdir ~/AP
cd ~/AP
```

Next, we create the DHCP server configuration file (`sudo nano dnsmasq.conf`) and its contents will be as follows:
```bash
interface=wlp3s0
dhcp-range=172.16.0.2,172.16.0.5,255.255.255.0,24h
server=8.8.8.8
```

Where we define the name of the WLAN interface, the range of IPs that will be assigned to devices connecting to the AP, and configure the DNS for the connected devices.

Finally, in step 2, we'll load the created configuration into the dnsmasq service.
```bash
sudo dnsmasq -C dnsmasq.conf
```

#### **Step 3: Enabling Internet Connection for Devices** 
We enable IP forwarding and sets up NAT routing from the Ethernet interface to the wireless interface, granting internet access to devices connected to the AP.
```bash
sudo sysctl -w net.ipv4.ip_forward=1
sudo iptables -t nat -A POSTROUTING -o enp4s0 -j MASQUERADE
```

#### **Step 4: Running the Access Point**  
In the fourth and final step, we run the file main.py (which you can find in the src folder and we will put it in the folder we created earlier (/AP)), which initializes the AP and the management console:
```bash
sudo python3 main.py
```

Now we have created the AP, which in our case, we have assigned the name X, and we can now connect to it from any device if its MAC address is among the MAC addresses that the AP accepts and within the specified time frames.

## Design, implementation and results

The design, implementation and results of this project are explained in [doc/REPORT.md](doc/REPORT.md). The aim of that document is to explain the main functionalities implemented for our program, as well as the resulting menu that allows to control all the system.


# CyberNet Labs — Decentralized VPN Using Blockchain (GUI)

**Version 1.0**  
**Developed by CyberNet Labs**

## Overview

CyberNet Labs Decentralized VPN combines peer-to-peer VPN tunnels with a simple on-disk blockchain ledger. Peers can **rent** or **share** bandwidth in a trustless network: all deposits and usage charges are immutably recorded in a local blockchain. A sleek, Apple-inspired GUI makes it easy to switch between **Provider** and **Client** modes and watch real-time logs.

## Features

- **Provider Mode**  
  Advertise your bandwidth on a chosen port. Clients deposit tokens and stream through your node.

- **Client Mode**  
  Connect to a provider, deposit tokens, and send data over a secure SSL/TLS tunnel.

- **Blockchain Ledger**  
  Records every `deposit` and `usage` transaction in `vpn_ledger.json` with Proof-of-Work, ensuring transparency.

- **SSL/TLS Encryption**  
  All VPN traffic runs over self-signed certificates (generate with OpenSSL).

- **Apple-Style GUI**  
  Modern, minimalist interface built with Tkinter + ttk—no extra dependencies.

- **Cross-Platform**  
  Runs on macOS, Windows, Linux (Python 3.7+).

## Prerequisites

- Python 3.7 or higher  
- OpenSSL (for cert generation)

## Installation & Setup

1. **Clone the repo**  
   ```bash
   git clone https://github.com/your-username/decentralized-vpn-gui.git
   cd decentralized-vpn-gui
``
   ## 2.	Generate SSL cert/key
   ```bash
openssl req -newkey rsa:2048 -nodes -keyout server.key \
        -x509 -days 365 -out server.crt
```

## 3.	Run the app
```bash
python cnl_vpn_gui.py
```

## Using the GUI
	1.	Select Mode
	•	Provider: Enter bind port (e.g. 9000) and rate (tokens/MB), then click Start Provider.
	•	Client: Enter provider IP, port, deposit amount, then click Connect Client.
	2.	Console Pane
	•	Shows deposits, session start/end, data usage, and block mining.
	•	Client echoes appear prefixed with ↩.
	3.	Inspect the Ledger
	•	Open vpn_ledger.json to view all blocks and transactions.

## Example Workflow
	•	As Provider
	1.	Launch GUI → Mode: Provider → Port 9000, Rate 10 → Start Provider
	2.	Console logs “Provider listening on 0.0.0.0:9000”
	•	As Client
	1.	Launch GUI → Mode: Client → Host 192.168.1.5, Port 9000, Deposit 50 → Connect Client
	2.	Console logs “Connected to 192.168.1.5:9000” → Type messages to simulate VPN traffic

 ## Notes & Next Steps
	•	Self-signed certs will trigger warnings in browsers—this is expected for testing.
	•	Ensure any firewalls allow inbound connections on your chosen port.
	•	For production, replace the local blockchain with a full distributed ledger and use valid SSL certificates.

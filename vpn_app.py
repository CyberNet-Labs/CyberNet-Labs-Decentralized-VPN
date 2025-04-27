#!/usr/bin/env python3
"""
CyberNet Labs — Decentralized VPN via Blockchain
Run as **provider** to rent out bandwidth, or as **client** to consume it.
"""

import ssl
import socket
import threading
import argparse
import os
import time
from blockchain import Blockchain

BANNER = r"""
   ____    _                   _   _   _        _    
  / ___|  (_) ___ ___  _ __   | | | | | |  ___ | | __
 | |  _   | |/ __/ _ \| '_ \  | | | | | | / _ \| |/ /
 | |_| |  | | (_| (_) | | | | | |_| | | ||  __/|   < 
  \____| _/ |\___\___/|_| |_|  \___/  |_| \___||_|\_\
        |__/    Decentralized VPN (CyberNet Labs)
"""

LEDGER_FILE = 'vpn_ledger.json'
CERT_FILE   = 'server.crt'
KEY_FILE    = 'server.key'

def banner():
    print(BANNER)

def start_provider(bind_ip, port, rate_per_mb):
    bc = Blockchain(LEDGER_FILE)
    print(f"[+] Loaded ledger: {LEDGER_FILE}")
    # SSL context
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(CERT_FILE, KEY_FILE)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((bind_ip, port))
    sock.listen(5)
    print(f"[*] Provider listening on {bind_ip}:{port}, rate {rate_per_mb} tokens/MB")

    while True:
        client, addr = sock.accept()
        ssl_client = ctx.wrap_socket(client, server_side=True)
        print(f"[+] Client connected: {addr[0]}")
        threading.Thread(
            target=handle_session,
            args=(ssl_client, addr[0], bc, rate_per_mb),
            daemon=True
        ).start()

def handle_session(conn, client_ip, bc, rate_per_mb):
    """
    Protocol:
    1) Client sends 8-byte deposit amount (float, ASCII)
    2) Record deposit
    3) Echo loop: receive data, send back, count bytes
    4) On EOF: compute usage, record usage tx, finalize block
    """
    try:
        deposit = float(conn.recv(32).decode().strip())
    except:
        conn.close(); return

    print(f"[>] Deposit: {deposit} tokens from {client_ip}")
    bc.new_transaction(sender=client_ip, recipient='provider', amount=deposit, tx_type='deposit')

    bytes_used = 0
    start = time.time()

    while True:
        data = conn.recv(4096)
        if not data:
            break
        bytes_used += len(data)
        conn.sendall(data)  # echo back as demo

    mb = bytes_used / (1024*1024)
    cost = mb * rate_per_mb
    print(f"[>] Session end: {mb:.3f} MB used, cost={cost:.3f} tokens")

    bc.new_transaction(sender='provider', recipient=client_ip, amount=cost, tx_type='usage')
    bc.new_block()
    conn.close()

def start_client(server_ip, port, deposit):
    bc = Blockchain(LEDGER_FILE)
    print(f"[+] Ledger: {LEDGER_FILE}")
    # record deposit intent
    bc.new_transaction(sender='client', recipient=server_ip, amount=deposit, tx_type='deposit')
    bc.new_block()

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ssl_sock = ctx.wrap_socket(sock, server_hostname=server_ip)
    ssl_sock.connect((server_ip, port))
    print(f"[*] Connected to provider {server_ip}:{port}")

    # send deposit
    ssl_sock.sendall(f"{deposit}".encode().ljust(32))

    print("Type messages. Empty line to end.")
    total = 0
    while True:
        line = input("> ").encode()
        if not line:
            break
        ssl_sock.sendall(line)
        resp = ssl_sock.recv(4096)
        total += len(line)
        print(f"↩ {resp.decode()}")

    ssl_sock.close()
    mb = total / (1024*1024)
    print(f"[+] You sent {mb:.3f} MB")
    # usage tx will be recorded by provider on their end

if __name__ == "__main__":
    banner()
    p = argparse.ArgumentParser()
    p.add_argument('mode', choices=['provider','client'])
    p.add_argument('--host',    default='0.0.0.0')
    p.add_argument('--port',    type=int, default=9000)
    p.add_argument('--rate',    type=float, default=10.0,
                   help="Tokens per MB (provider only)")
    p.add_argument('--deposit', type=float, default=100.0,
                   help="Deposit amount (client only)")
    args = p.parse_args()

    if args.mode == 'provider':
        start_provider(args.host, args.port, args.rate)
    else:
        server = args.host
        start_client(server, args.port, args.deposit)

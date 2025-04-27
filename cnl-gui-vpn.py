#!/usr/bin/env python3
"""
CyberNet Labs — Decentralized VPN Using Blockchain (Apple-Style GUI)
Version 1.0
Developed by CyberNet Labs
"""

import os
import time
import json
import ssl
import socket
import threading
import hashlib
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# === Constants ===
LEDGER_FILE    = 'vpn_ledger.json'
CERT_FILE      = 'server.crt'
KEY_FILE       = 'server.key'
BUFFER_SIZE    = 4096
DEFAULT_RATE   = 10.0    # tokens per MB

# === Ensure ledger exists ===
if not os.path.exists(LEDGER_FILE):
    with open(LEDGER_FILE, 'w') as f:
        json.dump([], f)

# === Blockchain ===
class Block:
    def __init__(self, index, timestamp, transactions, previous_hash, nonce=0):
        self.index          = index
        self.timestamp      = timestamp
        self.transactions   = transactions
        self.previous_hash  = previous_hash
        self.nonce          = nonce
    def compute_hash(self):
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

class Blockchain:
    difficulty = 3
    def __init__(self, fname=LEDGER_FILE):
        self.ledger_file = fname
        self.chain = []
        self.current_tx = []
        self.load_chain()
    def load_chain(self):
        with open(self.ledger_file,'r') as f:
            data = json.load(f)
        for blk in data:
            self.chain.append(Block(**blk))
        if not self.chain:
            self.new_block(previous_hash='0')
    def save_chain(self):
        with open(self.ledger_file,'w') as f:
            json.dump([b.__dict__ for b in self.chain], f, indent=2)
    def new_transaction(self, sender, recipient, amount, tx_type):
        tx = {'sender':sender,'recipient':recipient,
              'amount':amount,'type':tx_type,'timestamp':time.time()}
        self.current_tx.append(tx)
    def new_block(self, previous_hash=None):
        prev = previous_hash or self.chain[-1].compute_hash()
        blk = Block(len(self.chain), time.time(), self.current_tx, prev)
        blk.nonce = self.proof_of_work(blk)
        self.chain.append(blk)
        self.current_tx = []
        self.save_chain()
    def proof_of_work(self, block):
        block.nonce = 0
        h = block.compute_hash()
        target = '0'*self.difficulty
        while not h.startswith(target):
            block.nonce += 1
            h = block.compute_hash()
        return block.nonce

# === Networking Logic ===

def handle_session(conn, addr, rate, chain, status_cb):
    try:
        deposit = float(conn.recv(32).decode().strip())
    except:
        conn.close(); return
    status_cb(f"Client {addr} deposited {deposit} tokens")
    chain.new_transaction(addr, 'provider', deposit, 'deposit')
    used = 0
    while True:
        data = conn.recv(BUFFER_SIZE)
        if not data: break
        used += len(data)
        conn.sendall(data)
    mb = used/(1024*1024)
    cost = mb*rate
    status_cb(f"Client used {mb:.2f} MB → cost {cost:.2f}")
    chain.new_transaction('provider', addr, cost, 'usage')
    chain.new_block()
    conn.close()

def start_provider(host, port, rate, status_cb):
    chain = Blockchain()
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(CERT_FILE, KEY_FILE)
    srv = socket.socket()
    srv.bind((host, port))
    srv.listen(5)
    status_cb(f"Provider listening on {host}:{port}")
    while True:
        client, addr = srv.accept()
        ssl_c = ctx.wrap_socket(client, server_side=True)
        threading.Thread(
            target=handle_session,
            args=(ssl_c, addr[0], rate, chain, status_cb),
            daemon=True
        ).start()

def client_loop(host, port, deposit, status_cb, recv_cb):
    chain = Blockchain()
    chain.new_transaction('client', host, deposit, 'deposit')
    chain.new_block()
    status_cb(f"Deposited {deposit} tokens to {host}")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    sock = socket.socket()
    ssl_s = ctx.wrap_socket(sock, server_hostname=host)
    try:
        ssl_s.connect((host, port))
    except Exception as e:
        status_cb(f"Connect error: {e}"); return
    ssl_s.sendall(str(deposit).encode().ljust(32))
    status_cb(f"Connected to {host}:{port}")
    def recv_thread():
        while True:
            data = ssl_s.recv(BUFFER_SIZE)
            if not data: break
            recv_cb(data.decode(errors='ignore'))
    threading.Thread(target=recv_thread, daemon=True).start()
    return ssl_s

# === GUI ===

class VPNGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CyberNet Labs — Decentralized VPN")
        self.geometry("700x600")
        self.configure(bg="#ECECEC")
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        self._setup_styles()
        self._build_ui()
        self.sock = None

    def _setup_styles(self):
        s = self.style
        s.configure("Header.TLabel", bg="#ECECEC",
                    font=("Helvetica Neue",24,"bold"))
        s.configure("TFrame", bg="#ECECEC")
        s.configure("Card.TFrame", bg="white", relief="flat")
        s.configure("TLabel", bg="white", font=("Helvetica Neue",12))
        s.configure("TEntry", font=("Helvetica Neue",12))
        s.configure("Accent.TButton",
                    bg="#007AFF", fg="white",
                    font=("Helvetica Neue",13), padding=8)
        s.map("Accent.TButton",
              background=[("active","#005BBB")])

    def _build_ui(self):
        ttk.Label(self, text="CyberNet Labs VPN", style="Header.TLabel").pack(pady=(20,10))
        pnl = ttk.Frame(self); pnl.pack(fill="x", padx=30, pady=10)

        # Mode selection
        ttk.Label(pnl, text="Mode:", background="#ECECEC").grid(row=0,column=0,sticky="w")
        self.mode_cb = ttk.Combobox(pnl, values=["Provider","Client"], state="readonly")
        self.mode_cb.current(0); self.mode_cb.grid(row=0,column=1,sticky="ew")
        pnl.columnconfigure(1, weight=1)

        # Provider settings
        self.prov_frame = ttk.Frame(self, style="Card.TFrame")
        self.prov_frame.pack(fill="x", padx=30, pady=10)
        ttk.Label(self.prov_frame, text="Bind Port:", style="TLabel").grid(row=0,column=0,sticky="w",padx=10,pady=5)
        self.prov_port = ttk.Entry(self.prov_frame); self.prov_port.insert(0,"9000")
        self.prov_port.grid(row=0,column=1,sticky="ew",padx=10,pady=5)
        ttk.Label(self.prov_frame, text="Rate (tokens/MB):", style="TLabel").grid(row=1,column=0,sticky="w",padx=10,pady=5)
        self.prov_rate = ttk.Entry(self.prov_frame); self.prov_rate.insert(0,str(DEFAULT_RATE))
        self.prov_rate.grid(row=1,column=1,sticky="ew",padx=10,pady=5)
        self.prov_btn = ttk.Button(self.prov_frame, text="Start Provider",
                                   style="Accent.TButton", command=self._on_start_provider)
        self.prov_btn.grid(row=2,column=0,columnspan=2,pady=10)
        self.prov_frame.columnconfigure(1, weight=1)

        # Client settings
        self.cli_frame = ttk.Frame(self, style="Card.TFrame")
        ttk.Label(self.cli_frame, text="Server IP:", style="TLabel").grid(row=0,column=0,sticky="w",padx=10,pady=5)
        self.cli_host = ttk.Entry(self.cli_frame); self.cli_host.insert(0,"127.0.0.1")
        self.cli_host.grid(row=0,column=1,sticky="ew",padx=10,pady=5)
        ttk.Label(self.cli_frame, text="Port:", style="TLabel").grid(row=1,column=0,sticky="w",padx=10,pady=5)
        self.cli_port = ttk.Entry(self.cli_frame); self.cli_port.insert(0,"9000")
        self.cli_port.grid(row=1,column=1,sticky="ew",padx=10,pady=5)
        ttk.Label(self.cli_frame, text="Deposit:", style="TLabel").grid(row=2,column=0,sticky="w",padx=10,pady=5)
        self.cli_dep = ttk.Entry(self.cli_frame); self.cli_dep.insert(0,"100")
        self.cli_dep.grid(row=2,column=1,sticky="ew",padx=10,pady=5)
        self.cli_btn = ttk.Button(self.cli_frame, text="Connect Client",
                                   style="Accent.TButton", command=self._on_start_client)
        self.cli_btn.grid(row=3,column=0,columnspan=2,pady=10)
        self.cli_frame.columnconfigure(1, weight=1)

        # Console
        self.console = scrolledtext.ScrolledText(self, height=12, font=("Helvetica Neue",12), bd=0)
        self.console.pack(fill="both", expand=True, padx=30, pady=(0,20))
        self.mode_cb.bind("<<ComboboxSelected>>", lambda e:self._switch_mode())
        self._switch_mode()

    def _switch_mode(self):
        self.prov_frame.pack_forget()
        self.cli_frame.pack_forget()
        if self.mode_cb.get()=="Provider":
            self.prov_frame.pack(fill="x", padx=30, pady=10)
        else:
            self.cli_frame.pack(fill="x", padx=30, pady=10)

    def _on_start_provider(self):
        try:
            port = int(self.prov_port.get())
            rate = float(self.prov_rate.get())
        except:
            messagebox.showerror("Invalid input","Please enter valid port and rate.")
            return
        threading.Thread(
            target=start_provider,
            args=("0.0.0.0", port, rate, self._log),
            daemon=True
        ).start()
        self.prov_btn.config(state="disabled")

    def _on_start_client(self):
        try:
            host = self.cli_host.get()
            port = int(self.cli_port.get())
            deposit = float(self.cli_dep.get())
        except:
            messagebox.showerror("Invalid input","Please enter valid host, port, and deposit.")
            return
        sock = client_loop(host, port, deposit, self._log, self._display)
        if sock:
            self.sock = sock
            self.cli_btn.config(state="disabled")

    def _log(self, msg):
        timestamp = time.strftime("%H:%M:%S")
        self.console.insert("end", f"[{timestamp}] {msg}\n")
        self.console.see("end")

    def _display(self, data):
        self.console.insert("end", f"↩ {data}\n")
        self.console.see("end")

if __name__ == "__main__":
    VPNGUI().mainloop()

#!/usr/bin/env python3
"""
CyberNet Labs — Simple Blockchain Ledger
Tracks VPN rental deposits, usage, and reputation.
"""

import hashlib
import json
import time
import os

class Block:
    def __init__(self, index, timestamp, transactions, previous_hash, nonce=0):
        self.index          = index
        self.timestamp      = timestamp
        self.transactions   = transactions  # list of dicts
        self.previous_hash  = previous_hash
        self.nonce          = nonce

    def compute_hash(self):
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()


class Blockchain:
    difficulty = 3  # adjust for faster/slower PoW

    def __init__(self, ledger_file='ledger.json'):
        self.chain               = []
        self.current_transactions = []
        self.ledger_file         = ledger_file
        if os.path.exists(ledger_file):
            self._load_chain()
        else:
            # create genesis block
            self.new_block(previous_hash='0')

    def _load_chain(self):
        with open(self.ledger_file, 'r') as f:
            data = json.load(f)
            for blk in data:
                self.chain.append(Block(**blk))

    def _save_chain(self):
        with open(self.ledger_file, 'w') as f:
            json.dump([blk.__dict__ for blk in self.chain], f, indent=2)

    def new_transaction(self, sender, recipient, amount, tx_type):
        """
        tx_type: 'deposit' or 'usage'
        """
        tx = {
            'sender'    : sender,
            'recipient' : recipient,
            'amount'    : amount,
            'type'      : tx_type,
            'timestamp' : time.time()
        }
        self.current_transactions.append(tx)
        return self.last_block.index + 1

    def new_block(self, previous_hash=None):
        block = Block(
            index        = len(self.chain),
            timestamp    = time.time(),
            transactions = self.current_transactions,
            previous_hash= previous_hash or self.last_block.compute_hash()
        )
        # proof of work
        block.nonce = self.proof_of_work(block)
        self.chain.append(block)
        self.current_transactions = []
        self._save_chain()
        return block

    def proof_of_work(self, block):
        block.nonce = 0
        computed_hash = block.compute_hash()
        target = '0' * self.difficulty
        while not computed_hash.startswith(target):
            block.nonce += 1
            computed_hash = block.compute_hash()
        return block.nonce

    @property
    def last_block(self):
        return self.chain[-1]

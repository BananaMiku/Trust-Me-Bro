#!/usr/bin/env python3

import hashlib
import yaml
from typing import Dict

class PCRVerifier:
    def __init__(self):
        self.pcr_banks = {
            'sha1': {},
            'sha256': {},
            'sha384': {},
            'sha512': {}
        }
        self.initialize_pcrs()

    def initialize_pcrs(self):
        """Initialize all PCRs to zero for each hash algorithm."""
        for bank in self.pcr_banks.keys():
            for pcr in range(24):  # TPM typically has PCRs 0-23
                if bank == 'sha1':
                    self.pcr_banks[bank][pcr] = b'\x00' * 20
                elif bank == 'sha256':
                    self.pcr_banks[bank][pcr] = b'\x00' * 32
                elif bank == 'sha384':
                    self.pcr_banks[bank][pcr] = b'\x00' * 48
                elif bank == 'sha512':
                    self.pcr_banks[bank][pcr] = b'\x00' * 64

    def extend_pcr(self, pcr_index: int, algorithm: str, digest: str) -> None:
        """
        Extend a PCR with a new measurement.
        
        Args:
            pcr_index: The index of the PCR to extend
            algorithm: The hash algorithm to use (sha1, sha256, sha384, or sha512)
            digest: The hex string of the digest to extend with
        """
        if algorithm not in self.pcr_banks:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")
        
        current_value = self.pcr_banks[algorithm][pcr_index]
        digest_bytes = bytes.fromhex(digest)
        
        # Create a new hash object of the specified algorithm
        hasher = getattr(hashlib, algorithm)()
        # Extend is defined as: PCRnew = Hash(PCRold || digest)
        hasher.update(current_value + digest_bytes)
        
        # Update the PCR with the new value
        self.pcr_banks[algorithm][pcr_index] = hasher.digest()

    def get_pcr_value(self, pcr_index: int, algorithm: str) -> str:
        """Get the current value of a PCR as a hex string."""
        if algorithm not in self.pcr_banks:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")
        return self.pcr_banks[algorithm][pcr_index].hex()

def main():
    verifier = PCRVerifier()
    with open("shared/imalog.txt", "r") as ima_log:
        while line := ima_log.readline():
            digest = line.split(" ")[1]
            # digest = bytes.fromhex(digest)
            verifier.extend_pcr(10, "sha1", digest)
    print(verifier.get_pcr_value(10, "sha1"))

if __name__ == "__main__":
    exit(main())
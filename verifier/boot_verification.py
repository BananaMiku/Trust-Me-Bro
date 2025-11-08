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

    def verify_boot_log(self, log_file: str) -> Dict[str, Dict[int, bytes]]:
        """
        Verify a boot log file by simulating PCR extensions and comparing results.
        
        Args:
            log_file: Path to the YAML boot log file
            
        Returns:
            Dictionary mapping hash algorithms to PCR values
        """
        with open(log_file, 'r') as f:
            log_data = yaml.safe_load(f)

        # Process each event in the log
        for event in log_data['events']:
            pcr_index = event['PCRIndex']
            
            # Handle different digest formats in the log
            if 'DigestCount' in event:
                # Multiple digests per event
                for digest_entry in event['Digests']:
                    algo = digest_entry['AlgorithmId'].lower()
                    if algo in self.pcr_banks:
                        self.extend_pcr(pcr_index, algo, digest_entry['Digest'])
            elif 'Digest' in event:
                # Single digest format
                algo = event.get('Algorithm', 'sha1').lower()
                if algo in self.pcr_banks:
                    self.extend_pcr(pcr_index, algo, event['Digest'])

        return self.pcr_banks

    def get_pcr_value(self, pcr_index: int, algorithm: str) -> str:
        """Get the current value of a PCR as a hex string."""
        if algorithm not in self.pcr_banks:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")
        return self.pcr_banks[algorithm][pcr_index].hex()

def main():
    verifier = PCRVerifier()
    
    # Path to the boot log file
    boot_log_file = "shared/boot_log.yaml"
    
    try:
        # Verify the boot log
        final_pcrs = verifier.verify_boot_log(boot_log_file)
        
        # Print the final PCR values
        print("Final PCR values after processing boot log:")
        for algo in sorted(final_pcrs.keys()):
            print(f"\n{algo.upper()} PCR values:")
            for pcr_index in range(24):
                if final_pcrs[algo][pcr_index] != b'\x00' * len(final_pcrs[algo][pcr_index]):
                    print(f"PCR{pcr_index}: {final_pcrs[algo][pcr_index].hex()}")
                    
    except Exception as e:
        print(f"Error verifying boot log: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

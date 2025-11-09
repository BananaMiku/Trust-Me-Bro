#!/usr/bin/env python3

import hashlib
import yaml
from typing import Dict
import struct

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

bootroot="shared"
def main():
    verifier = PCRVerifier()

    with open(f"{bootroot}/tpm2_pcr.yaml", "r") as signature_yaml:
        signature = yaml.safe_load(signature_yaml)
    print(f"{signature=}")


    # Ensure boot logs have valid hashes and such
    with open(f"{bootroot}/secure_boot", "rb") as secure_boot:
        pcr_index = struct.unpack("<I", secure_boot.read(4))[0]
        print(f"{pcr_index=}")
        event_type = struct.unpack("<I", secure_boot.read(4))[0]
        print(f"{event_type=}")
        initial_digest =  secure_boot.read(20)
        print(f"{initial_digest=}")
        event_size = struct.unpack("<I", secure_boot.read(4))[0]
        print(f"{event_size=}")
        event_data = secure_boot.read(event_size + 4)
        print(f"{event_data.hex()=}")
        # TODO finish parsing

    # Ensure that

    with open(f"{bootroot}/secure_boot.yaml", "r") as secure_boot_yaml:
        log_data = yaml.safe_load(secure_boot_yaml)

    # Process each event in the log
    for event in log_data['events']:
        pcr_index = event['PCRIndex']
        
        # Handle different digest formats in the log
        if 'DigestCount' in event:
            # Multiple digests per event
            for digest_entry in event['Digests']:
                algo = digest_entry['AlgorithmId'].lower()
                if algo in verifier.pcr_banks:
                    verifier.extend_pcr(pcr_index, algo, digest_entry['Digest'])
    

    # print(verifier.get_pcr_value(1, "sha1"))
    # print(verifier.get_pcr_value(2, "sha1"))
    # print(verifier.get_pcr_value(3, "sha1"))
    # print(verifier.get_pcr_value(4, "sha1"))
    # print(verifier.get_pcr_value(5, "sha1"))
    # print(verifier.get_pcr_value(6, "sha1"))
    # print(verifier.get_pcr_value(7, "sha1"))
    # print(verifier.get_pcr_value(8, "sha1"))
    # print(verifier.get_pcr_value(9, "sha1"))

    # with open("shared/imalog.txt", "r") as ima_log:
    #     while line := ima_log.readline():
    #         pcr_index, digest = line.split(" ")[:2]
    #         pcr_index = int(pcr_index)
    #         # digest = bytes.fromhex(digest)
    #         verifier.extend_pcr(pcr_index, "sha1", digest)
    # print(verifier.get_pcr_value(10, "sha1"))
    # print(verifier.get_pcr_value(11, "sha1"))
    # print(verifier.get_pcr_value(12, "sha1"))

if __name__ == "__main__":
    exit(main())
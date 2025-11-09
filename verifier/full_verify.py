#!/usr/bin/env python3

import hashlib
import yaml
from typing import Dict
import struct
import ecdsa

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

    verifying_key = open(f"{bootroot}/signing_key.pem", "r").read()
    verifying_key = ecdsa.VerifyingKey.from_pem(verifying_key)

    print(f"{verifying_key.curve=}")

    signature = open(f"{bootroot}/tpm2_pcr_signature", "rb").read()
    print(f"{signature.hex()=}")

    pcr_summary = open(f"{bootroot}/tpm2_pcr_message", "rb").read()
    print(f"{pcr_summary.hex()=}")

    pcr_data = open(f"{bootroot}/tpm2_pcr_data", "rb").read()
    print(f"{pcr_data.hex()=}")

    verifying_key.verify(signature, pcr_summary, hashfunc=hashlib.sha256, sigdecode=ecdsa.util.sigdecode_der)
    # verifying_key.verify(signature, pcr_summary, sigdecode=ecdsa.util.sigdecode_der)

    exit(0)


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

    # Ensure that signature corresponds to data

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
    
    for i in range(1, 10):
        calculated_pcr_value = verifier.get_pcr_value(i, "sha1")
        signed_pcr_value = signature["pcrs"]["sha1"][i]
        signed_pcr_value = signed_pcr_value.to_bytes(20)
        signed_pcr_value = signed_pcr_value.hex()
        # print(f"expected PCR{i}={signed_pcr_value}")
        # print(f"actual   PCR{i}={calculated_pcr_value}")
        assert calculated_pcr_value == signed_pcr_value
    
    print("PCR values match!")

    # Validate Measurement Log
    with open(f"{bootroot}/measurements", "rb") as measurements_file:
        while True:
            first_chunk = measurements_file.read(4)
            if not first_chunk:
                break
            pcr_index = struct.unpack("<I", first_chunk)[0]
            # print(f"{pcr_index=}")
            template_data_hash = measurements_file.read(20)
            # print(f"{template_data_hash.hex()=}")
            template_name_length = struct.unpack("<I", measurements_file.read(4))[0]
            # print(f"{template_name_length=}")
            template_name = measurements_file.read(template_name_length)
            # print(f"{template_name=}")
            template_data_length = struct.unpack("<I", measurements_file.read(4))[0]
            # print(f"{template_data_length=}")
            template_data = measurements_file.read(template_data_length)
            # print(f"{template_data=}")
            hash_algorithm = hashlib.sha1()
            hash_algorithm.update(template_data)
            actual_hash = hash_algorithm.digest()
            # print(f"{actual_hash.hex()=}")

            # print(f"expected digest={template_data_hash}")
            # print(f"actual   digest={actual_hash}")
            assert template_data_hash == actual_hash or template_data_hash == b"\x00" * 20
    
    print("Measurement log hash values match!")





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
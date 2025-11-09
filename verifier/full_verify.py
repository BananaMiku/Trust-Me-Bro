#!/usr/bin/env python3

import hashlib
import yaml
from typing import Dict
import struct
import ecdsa
import os
import re

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

    def get_pcr_value(self, pcr_index: int, algorithm: str) -> bytes:
        """Get the current value of a PCR as a hex string."""
        if algorithm not in self.pcr_banks:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")
        return self.pcr_banks[algorithm][pcr_index]

def parse_ima_ng(data_bytes: bytes):
    data_hash_length = struct.unpack("<I", data_bytes[:4])[0]
    data_hash_algorithm = data_bytes[4 : 4 + data_hash_length].split(b"\x00")[0]
    data_hash = data_bytes[4 + len(data_hash_algorithm) + 1 : 4 + data_hash_length]
    name_length = struct.unpack("<I", data_bytes[4 + data_hash_length : 4 + data_hash_length + 4])[0]
    name = data_bytes[4 + data_hash_length + 4 : 4 + data_hash_length + 4 + name_length - 1]
    return data_hash, name

bootroot="shared"
def main():
    verifier = PCRVerifier()

    pcr_data = open(f"{bootroot}/tpm2_pcr_data", "rb").read()
    expected_pcr_values = []
    print("===PCR Report===")
    for i in range(13):
        print(f"PCR{i:02d}: {pcr_data[20 * i: 20 * i + 20].hex()}")
        expected_pcr_values.append(pcr_data[20 * i: 20 * i + 20])
    print("===END PCR Report===")

    pcr_summary = open(f"{bootroot}/tpm2_pcr_message", "rb").read()

    quote_hash_algorithm = hashlib.sha256
    calculated_pcr_hash = quote_hash_algorithm()
    calculated_pcr_hash.update(pcr_data)
    calculated_pcr_hash = calculated_pcr_hash.digest()

    expected_pcr_hash = pcr_summary[-len(calculated_pcr_hash):]
    assert(calculated_pcr_hash == expected_pcr_hash)
    print("PCR banks match quote")

    verifying_key = open(f"{bootroot}/signing_key.pem", "rb").read()
    verifying_key = ecdsa.VerifyingKey.from_pem(verifying_key)

    signature = open(f"{bootroot}/tpm2_pcr_signature", "rb").read()

    verifying_key.verify(signature, pcr_summary, hashfunc=quote_hash_algorithm, sigdecode=ecdsa.util.sigdecode_der)
    print("signature of quote verified against key")

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
        event_data = secure_boot.read(event_size)
        print(f"{event_data.hex()=}")

        secure = False
        while secure_boot.read(1):
            secure_boot.seek(-1, os.SEEK_CUR)
            pcr_index = struct.unpack("<I", secure_boot.read(4))[0]
            print(f"{pcr_index=}")
            event_type = struct.unpack("<I", secure_boot.read(4))[0]
            print(f"{event_type=}")
            digest_count = struct.unpack("<I", secure_boot.read(4))[0]
            print(f"{digest_count=}")
            digest_dump = secure_boot.read(172)
            print(f"{digest_dump.hex()=}")
            event_size = struct.unpack("<I", secure_boot.read(4))[0]
            print(f"{event_size=}")
            event_data = secure_boot.read(event_size)
            # this is a terrible business logic but this is a hackathon
            try:
                if re.search("/boot/vmlinuz.*lsm=integrity ima_policy=tcb", event_data.decode(encoding="ascii")):
                    print(f"{event_data=}")
            except:
                pass


    # Ensure that signature corresponds to data

    secure_boot_logs = open(f"{bootroot}/secure_boot.yaml", "rb")
    secure_boot_logs = yaml.safe_load(secure_boot_logs)

    # Process each event in the log
    for event in secure_boot_logs['events']:
        pcr_index = event['PCRIndex']
        
        # Handle different digest formats in the log
        if 'DigestCount' in event:
            # Multiple digests per event
            for digest_entry in event['Digests']:
                algo = digest_entry['AlgorithmId'].lower()
                if algo in verifier.pcr_banks:
                    verifier.extend_pcr(pcr_index, algo, digest_entry['Digest'])
    
    for i in range(10):
        calculated_pcr_value = verifier.get_pcr_value(i, "sha1")
        expected_pcr_value = expected_pcr_values[i]
        assert calculated_pcr_value == expected_pcr_value
    
    print("PCR is consistent with boot log")

    # Validate Measurement Log
    matches = set()
    latest_file_hashes = dict()
    with open(f"{bootroot}/measurements", "rb") as measurements_file:
        # TODO add crypto business logic
        while measurements_file.read(1):
            measurements_file.seek(-1, os.SEEK_CUR)

            pcr_index = struct.unpack("<I", measurements_file.read(4))[0]
            template_data_hash = measurements_file.read(20)
            template_name_length = struct.unpack("<I", measurements_file.read(4))[0]
            template_name = measurements_file.read(template_name_length)
            template_data_length = struct.unpack("<I", measurements_file.read(4))[0]
            template_data = measurements_file.read(template_data_length)

            if pcr_index in matches:
                continue

            if template_name == b"ima-ng":
                file_data_hash, file_name = parse_ima_ng(template_data)
                # print(f"{file_data_hash.hex()=}")
                # print(f"{file_name=}")
                if file_data_hash != b"\x00" * 20:
                    latest_file_hashes[file_name] = file_data_hash

            hash_algorithm = hashlib.sha1()
            hash_algorithm.update(template_data)
            actual_hash = hash_algorithm.digest()

            # print(f"{actual_hash.hex()=}")

            # print(f"expected digest={template_data_hash}")
            # print(f"actual   digest={actual_hash}")
            assert template_data_hash == actual_hash or template_data_hash == b"\x00" * 20

            # This is an important undocumented quirk I found when looking at 
            actual_extension = b"\xff" * 20 if template_data_hash == b"\x00" * 20 else template_data_hash
            verifier.extend_pcr(pcr_index, "sha1", actual_extension.hex())
    
            for i in range(10, 13):
                calculated_pcr_value = verifier.get_pcr_value(i, "sha1")
                expected_pcr_value = expected_pcr_values[i]
                if calculated_pcr_value == expected_pcr_value:
                    matches.add(i)

    assert matches == set(range(10, 13)), set(range(10, 13)) - matches

    print("Measurement log hash values match!")

    audit_log_hash = hashlib.sha256()
    with open(f"{bootroot}/audit_log.txt", "rb") as audit_log_file:
        while line := audit_log_file.readline():
            audit_log_hash.update(line)
            current_audit_log_hash = audit_log_hash.digest()
            if current_audit_log_hash == latest_file_hashes[b"/var/log/audit/audit.log"]:
                break
        else:
            assert False, "audit log is not attested to!"
    print("audit log verified!")

    # TODO add business logic

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
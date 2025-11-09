#!/bin/bash

# This is the template for triggering a read (adding a file to the measurement log)
# sudo dd if=<file name> of=/dev/null count=0 status=none

usage() {
    echo "Usage: $0 -o OUTPUT_ZIP"
    echo
    echo "Options:"
    echo "  -o OUTPUT_ZIP    Path where the output zip file will be saved (required)"
    echo "  -h              Display this help message"
    exit 1
}

cleanup() {
    # Remove temporary directory if it exists
    if [ -n "$TARGET_FOLDER" ] && [ -d "$TARGET_FOLDER" ]; then
        rm -rf "$TARGET_FOLDER"
    fi
}

EK_HANDLE=./primary.ctx

# Create temporary directory
TARGET_FOLDER=$(mktemp -d)
if [ $? -ne 0 ]; then
    echo "Error: Failed to create temporary directory" >&2
    exit 1
fi

# Set up cleanup on script exit now that TARGET_FOLDER exists
trap cleanup EXIT

OUTPUT_ZIP=""

# Parse command line options
while getopts "o:h" opt; do
    case $opt in
        o)
            OUTPUT_ZIP="$OPTARG"
            ;;
        h)
            usage
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            usage
            ;;
        :)
            echo "Option -$OPTARG requires an argument." >&2
            usage
            ;;
    esac
done

# Check if OUTPUT_ZIP is provided
if [ -z "$OUTPUT_ZIP" ]; then
    echo "Error: OUTPUT_ZIP (-o) is required" >&2
    usage
fi

# Check if the directory for OUTPUT_ZIP exists and is writable
OUTPUT_DIR=$(dirname "$OUTPUT_ZIP")
if [ ! -d "$OUTPUT_DIR" ]; then
    echo "Error: Directory for output zip ($OUTPUT_DIR) does not exist" >&2
    exit 1
fi

if [ ! -w "$OUTPUT_DIR" ]; then
    echo "Error: Directory for output zip ($OUTPUT_DIR) is not writable" >&2
    exit 1
fi

# Since Virtualbox does not add a root EK, we create our own key for mocking purposes
sudo tpm2_createprimary -C e -g sha1 -G ecc -a "decrypt|sign|fixedtpm|fixedparent|sensitivedataorigin|userwithauth" -c $EK_HANDLE | sudo tee $TARGET_FOLDER/key_params.yaml

# Export the public key
sudo tpm2_readpublic -c $EK_HANDLE -o $TARGET_FOLDER/signing_key.pem -f pem

# Export the boot logs
sudo cat /sys/kernel/security/tpm0/binary_bios_measurements | sudo tee $TARGET_FOLDER/secure_boot
sudo tpm2_eventlog /sys/kernel/security/tpm0/binary_bios_measurements | sudo tee $TARGET_FOLDER/secure_boot.yaml

# Export the audit log and add it to the event log
sudo -g evtlogger -u root cp /var/log/audit/audit.log $TARGET_FOLDER/audit_log.txt

# Export the audit log and add it to the event log
sudo -g evtlogger -u root cp /etc/audit/rules.d/audit.rules $TARGET_FOLDER/audit.rules

# Sign the event log and export the signature of the event log
sudo tpm2_quote -c $EK_HANDLE -l sha1:0,1,2,3,4,5,6,7,8,9,10,11,12 -f plain --pcrs_format="values" -s $TARGET_FOLDER/tpm2_pcr_signature -m $TARGET_FOLDER/tpm2_pcr_message -o $TARGET_FOLDER/tpm2_pcr_data | sudo tee $TARGET_FOLDER/tpm2_pcr.yaml

# Export the event log
sudo cat /sys/kernel/security/integrity/ima/ascii_runtime_measurements_sha1 | sudo tee $TARGET_FOLDER/measurements_ascii.txt
sudo cat /sys/kernel/security/integrity/ima/binary_runtime_measurements_sha1 | sudo tee $TARGET_FOLDER/measurements

# Convert OUTPUT_ZIP to absolute path if it isn't already
if [[ "$OUTPUT_ZIP" != /* ]]; then
    OUTPUT_ZIP="$(pwd)/$OUTPUT_ZIP"
fi

# Create zip archive of all collected data
cd "$TARGET_FOLDER" && sudo zip -r "$OUTPUT_ZIP" ./*
if [ $? -ne 0 ]; then
    echo "Error: Failed to create zip archive" >&2
    exit 1
fi

echo "Successfully created measurement archive: $OUTPUT_ZIP"

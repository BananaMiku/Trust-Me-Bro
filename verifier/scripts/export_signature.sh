#!/bin/bash

# This is the template for triggering a read (adding a file to the measurement log)
# sudo dd if=<file name> of=/dev/null count=0 status=none

EK_HANDLE=./primary.ctx
TARGET_FOLDER=/home/maxwell/shared

# Since Virtualbox does not add a root EK, we create our own key for mocking purposes
sudo tpm2_createprimary -C e -g sha1 -G ecc -a "decrypt|sign|fixedtpm|fixedparent|sensitivedataorigin|userwithauth" -c $EK_HANDLE

# Export the boot process
sudo cat /sys/kernel/security/tpm0/binary_bios_measurements | sudo tee $TARGET_FOLDER/secure_boot
sudo tpm2_eventlog /sys/kernel/security/tpm0/binary_bios_measurements | sudo tee $TARGET_FOLDER/secure_boot.yaml

# Export the audit log and add it to the event log
sudo cp /var/log/audit/audit.log $TARGET_FOLDER/audit_log.txt

# Sign the event log and export the signature of the event log
sudo tpm2_quote -c $EK_HANDLE -l sha1:1,2,3,4,5,6,7,8,9,10,11,12 -s $TARGET_FOLDER/tpm2_pcr_signature -o $TARGET_FOLDER/tpm2_pcr_data | sudo tee $TARGET_FOLDER/tpm2_pcr.yaml

# Export the event log
sudo cat /sys/kernel/security/integrity/ima/ascii_runtime_measurements | sudo tee $TARGET_FOLDER/imalog.txt


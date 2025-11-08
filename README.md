# Trust Me Bro

## Members: 
Bennett Gillig, Austin Henlotter, Junyang Lu, Marshall Rhodes, Maxwell Tang, Steven Zhang

**Trust Me Bro** is a system that allows AI model providers to prove that each inference request was executed by the model and hardware they claim to be using.
By combining hardware-level attestation (TPM, IMA) with runtime profiling of GPU power draw, VRAM usage, and process integrity, the framework creates a verifiable audit trail for every inference.
The result: end users, auditors, or partners can trust that “Model X” actually ran on the stated hardware — not a cheaper, spoofed, or downgraded model.

__Motivation__
Modern AI services rely on trust: users assume that an API call to “Model A” really uses that model. However, without transparency, a provider could silently serve cheaper or smaller models while charging for premium ones.
This framework addresses that trust gap by providing cryptographic, runtime-verifiable proofs of inference integrity — forming the basis for “proof of inference authenticity.”

__How It Works__
1. 

__Key Features__


__Tech Stack__

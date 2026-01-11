# Panoglin

## Using Ed25519 API Keys

This guide explains how to generate an Ed25519 key pair using OpenSSL for API authentication.

### Step 0: Prerequisites

Ensure that OpenSSL is installed on your system.

```bash
sudo apt-get update
sudo apt-get install openssl
```

### Step 1: Generate the private key test-prv-key.pem. Do not share this file with anyone!

```bash
openssl genpkey -algorithm ed25519 -out private_key.pem
```

### Step 2: Compute the public key test-pub-key.pem from the private key.

```bash
openssl pkey -pubout -in private_key.pem -out public_key.pem
```

The public key should look something like this:

```bash
-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEACeCSz7VJkh3Bb+NF794hLMU8fLB9Zr+/tGMdVKCC2eo=
-----END PUBLIC KEY-----
```

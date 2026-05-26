# Password Transport Modes

## Recommended production mode

The default mode is `plain`.

In this mode, HTTPS/TLS protects password transport and Django `make_password` / `check_password` protects password storage.

```json
{
  "backend": {
    "password_transport_mode": "plain"
  }
}
```

## Optional compliance mode

The optional mode is `rsa_oaep`.

This mode is only a transport wrapper. The frontend sends a base64 RSA-OAEP-SHA256 ciphertext. The backend decrypts the payload into the raw password and still uses Django `make_password` / `check_password` for storage and verification.

Do not store or compare RSA ciphertext as a password-equivalent secret.
Do not write password payloads, ciphertext, or decrypted plaintext into logs or audit request payloads.

```json
{
  "backend": {
    "password_transport_mode": "rsa_oaep",
    "password_rsa_private_key_file": "/etc/ns_evermore/password_transport_private.pem",
    "password_transport_max_payload_length": 4096,
    "password_plaintext_max_length": 256
  }
}
```

You can also provide the private key via environment variables:

```bash
export NS_PASSWORD_TRANSPORT_MODE="rsa_oaep"
export NS_PASSWORD_RSA_PRIVATE_KEY_FILE="/etc/ns_evermore/password_transport_private.pem"
```

If the private key is passphrase-protected:

```bash
export NS_PASSWORD_RSA_PRIVATE_KEY_PASSPHRASE="change-me"
```

## Request contract

The request field name remains `password`.

- `plain`: `password` is the raw password.
- `rsa_oaep`: `password` is the base64 RSA-OAEP-SHA256 ciphertext.

This keeps API shape stable while making transport handling configurable on the backend.

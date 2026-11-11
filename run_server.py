"""
AstraTrack AI - HTTPS / SSL Server Launcher
Starts the Uvicorn ASGI server with TLS/SSL encryption for secure HTTPS access.

Server settings (host, port, SSL paths) are read from environment variables.
See .env.example for all supported variables.
"""

import sys
import os
import argparse
import datetime
import ipaddress
import uvicorn

# Load .env before reading any config
from backend.config import get_server_settings, get_ssl_cert_path, get_ssl_key_path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def ensure_ssl_certificates(cert_dir: str = "certs"):
    """Keep a public local CA certificate plus the HTTPS leaf/key; never persist the CA key."""
    os.makedirs(cert_dir, exist_ok=True)
    cert_path = os.path.join(cert_dir, "cert.pem")
    key_path = os.path.join(cert_dir, "key.pem")
    ca_path = os.path.join(cert_dir, "local_ca.crt")

    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.x509.oid import ExtendedKeyUsageOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization

        if all(os.path.exists(path) for path in (cert_path, key_path, ca_path)):
            try:
                with open(cert_path, "rb") as f:
                    existing_cert = x509.load_pem_x509_certificate(f.read())
                with open(key_path, "rb") as f:
                    existing_key = serialization.load_pem_private_key(f.read(), password=None)
                with open(ca_path, "rb") as f:
                    existing_ca = x509.load_pem_x509_certificate(f.read())
                now = datetime.datetime.now(datetime.timezone.utc)
                cert_key = existing_cert.public_key().public_bytes(
                    serialization.Encoding.DER,
                    serialization.PublicFormat.SubjectPublicKeyInfo,
                )
                private_key_public = existing_key.public_key().public_bytes(
                    serialization.Encoding.DER,
                    serialization.PublicFormat.SubjectPublicKeyInfo,
                )
                names = existing_cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
                eku = existing_cert.extensions.get_extension_for_class(x509.ExtendedKeyUsage).value
                if (cert_key == private_key_public
                        and existing_cert.not_valid_before_utc <= now < existing_cert.not_valid_after_utc
                        and x509.DNSName("localhost") in names
                        and ExtendedKeyUsageOID.SERVER_AUTH in eku
                        and existing_cert.issuer == existing_ca.subject
                        and existing_ca.extensions.get_extension_for_class(x509.BasicConstraints).value.ca
                        and not existing_cert.extensions.get_extension_for_class(x509.BasicConstraints).value.ca):
                    existing_cert.verify_directly_issued_by(existing_ca)
                    return cert_path, key_path
            except Exception:
                pass

        print("Generating a localhost HTTPS leaf certificate and a separate local trust certificate...")
        now = datetime.datetime.now(datetime.timezone.utc)
        ca_key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
        ca_subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "AstraTrack Local Development"),
            x509.NameAttribute(NameOID.COMMON_NAME, "AstraTrack Local HTTPS Root"),
        ])
        ca_cert = x509.CertificateBuilder().subject_name(
            ca_subject
        ).issuer_name(
            ca_subject
        ).public_key(
            ca_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            now - datetime.timedelta(minutes=5)
        ).not_valid_after(
            now + datetime.timedelta(days=3650)
        ).add_extension(
            x509.BasicConstraints(ca=True, path_length=0), critical=True
        ).add_extension(
            x509.KeyUsage(
                digital_signature=True, content_commitment=False,
                key_encipherment=False, data_encipherment=False,
                key_agreement=False, key_cert_sign=True, crl_sign=True,
                encipher_only=False, decipher_only=False,
            ), critical=True
        ).add_extension(
            x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key()), critical=False
        ).sign(ca_key, hashes.SHA256())

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        leaf_subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "AstraTrack AI"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])
        cert = x509.CertificateBuilder().subject_name(
            leaf_subject
        ).issuer_name(
            ca_subject
        ).public_key(
            key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            now - datetime.timedelta(minutes=5)
        ).not_valid_after(
            now + datetime.timedelta(days=1825)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1"))
            ]),
            critical=False
        ).add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True
        ).add_extension(
            x509.KeyUsage(
                digital_signature=True, content_commitment=False,
                key_encipherment=True, data_encipherment=False,
                key_agreement=False, key_cert_sign=False, crl_sign=False,
                encipher_only=False, decipher_only=False,
            ),
            critical=True
        ).add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),
            critical=False
        ).add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()),
            critical=False
        ).sign(ca_key, hashes.SHA256())

        with open(ca_path, "wb") as f:
            f.write(ca_cert.public_bytes(serialization.Encoding.PEM))
        with open(key_path, "wb") as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        print("Local HTTPS certificates generated. Trust the root for this Windows user with:")
        print("  powershell -ExecutionPolicy Bypass -File commands\\trust_local_https.ps1")
        return cert_path, key_path
    except Exception as e:
        print(f"⚠️ Could not auto-generate certificates: {e}")
        return None, None


if __name__ == "__main__":
    # ── Environment defaults (from .env / system env) ─────────────────────────
    _env_settings = get_server_settings()

    parser = argparse.ArgumentParser(description="AstraTrack AI Server Launcher")
    parser.add_argument("--http", action="store_true", help="Run without SSL (plain HTTP)")
    parser.add_argument("--init-certs", action="store_true", help="Create or validate the local HTTPS certificate, then exit")
    parser.add_argument(
        "--port", type=int,
        default=_env_settings["port"],
        help=f"Port to bind (default from env: {_env_settings['port']})"
    )
    parser.add_argument(
        "--host", type=str,
        default=_env_settings["host"],
        help=f"Host to bind (default from env: {_env_settings['host']})"
    )
    args = parser.parse_args()

    if args.init_certs:
        cert_path, key_path = ensure_ssl_certificates()
        if cert_path and key_path:
            print(f"Certificate: {cert_path}")
            print(f"Private key: {key_path}")
            raise SystemExit(0)
        raise SystemExit(1)

    use_https = not args.http
    cert_path, key_path = None, None

    if use_https:
        # Prefer SSL paths from environment, fall back to auto-generation
        env_cert = get_ssl_cert_path()
        env_key  = get_ssl_key_path()

        if env_cert and env_key and os.path.exists(env_cert) and os.path.exists(env_key):
            cert_path, key_path = env_cert, env_key
        else:
            cert_path, key_path = ensure_ssl_certificates()

        if not (cert_path and key_path):
            print("⚠️ Falling back to HTTP mode.")
            use_https = False

    protocol = "https" if use_https else "http"
    url = f"{protocol}://{args.host}:{args.port}"

    print("==========================================================")
    print("✨ AstraTrack AI - Millennium Sky & Trajectory Sentinel ✨")
    print("==========================================================")
    print(f"🚀 Launching Secure AI Interface on: {url}")
    print(f"🔒 Protocol: {protocol.upper()}")
    print(f"🌍 Environment: {_env_settings['env']}")
    if use_https:
        print(f"📜 Certificate: {cert_path}")
        print(f"🔑 Private Key:  {key_path}")
        print("💡 Note: Accept the self-signed certificate warning in your browser if prompted.")
    print("📡 Press Ctrl+C to terminate.")
    print("==========================================================")

    if use_https:
        uvicorn.run(
            "backend.main:app",
            host=args.host,
            port=args.port,
            ssl_keyfile=key_path,
            ssl_certfile=cert_path,
            reload=False,
        )
    else:
        uvicorn.run(
            "backend.main:app",
            host=args.host,
            port=args.port,
            reload=False,
        )

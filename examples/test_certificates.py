"""Tests for SSL certificate loading functionalities in PyAzul."""

import asyncio
import os

from pyazul.core.config import get_azul_settings


def print_separator():
    """Print a separator line to the console."""
    print("\n" + "=" * 60 + "\n")


async def test_certificates():
    """Tests the loading and verification of SSL certificates."""
    print_separator()
    print("1. Starting certificate test...")

    try:
        # First get the configuration to see debug messages
        print("\n2. Loading configuration...")
        settings = get_azul_settings()
        cert_path, key_path = settings._load_certificates()
        print("\nCertificates loaded:")
        print(f"- Certificate: {cert_path}")
        print(f"- Key: {key_path}")

        print("\n3. Verifying files...")
        await verify_certificate_loading()

    except Exception as e:
        print(f"\nError: {str(e)}")
        print("\nError details:")
        import traceback

        traceback.print_exc()
        raise


async def verify_certificate_loading():
    """Verify that certificates are loaded correctly."""
    print("\nVerifying certificate files:")

    # Get certificate paths
    settings = get_azul_settings()
    cert_path, key_path = settings._load_certificates()

    # Verify existence
    print("\nFile existence:")
    print(f"- Certificate exists: {os.path.exists(cert_path)}")
    print(f"- Key exists: {os.path.exists(key_path)}")

    # Verify permissions
    print("\nFile permissions:")
    cert_perms = oct(os.stat(cert_path).st_mode)[-3:]
    key_perms = oct(os.stat(key_path).st_mode)[-3:]
    print(f"- Certificate permissions: {cert_perms}")
    print(f"- Key permissions: {key_perms}")

    # Verify content
    print("\nCertificate content:")
    with open(cert_path, "r") as f:
        cert_content = f.read()
        print("- Has BEGIN marker:", "-----BEGIN CERTIFICATE-----" in cert_content)
        print("- Has END marker:", "-----END CERTIFICATE-----" in cert_content)
        print("- Length:", len(cert_content))

    print("\nKey content:")
    with open(key_path, "r") as f:
        key_content = f.read()
        print("- Has BEGIN marker:", "-----BEGIN PRIVATE KEY-----" in key_content)
        print("- Has END marker:", "-----END PRIVATE KEY-----" in key_content)
        print("- Length:", len(key_content))


if __name__ == "__main__":
    print("\nCertificate Loading Test")
    print("=" * 60)
    asyncio.run(test_certificates())

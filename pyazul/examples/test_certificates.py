import asyncio
import os
from pyazul.core.config import get_azul_settings

def print_separator():
    print("\n" + "=" * 60 + "\n")

async def test_certificates():
    print_separator()
    print("1. Iniciando prueba de certificados...")
    
    try:
        # Primero obtener la configuración para ver los mensajes de debug
        print("\n2. Cargando configuración...")
        settings = get_azul_settings()
        cert_path, key_path = settings._load_certificates()
        print("\nCertificados cargados:")
        print(f"- Certificado: {cert_path}")
        print(f"- Llave: {key_path}")
        
        print("\n3. Verificando archivos...")
        await verify_certificate_loading()
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("\nDetalles del error:")
        import traceback
        traceback.print_exc()
        raise

async def verify_certificate_loading():
    """Verify that certificates are loaded correctly."""
    print("\nVerificando archivos de certificados:")
    
    # Obtener rutas de los certificados
    settings = get_azul_settings()
    cert_path, key_path = settings._load_certificates()
    
    # Verificar existencia
    print("\nExistencia de archivos:")
    print(f"- Certificado existe: {os.path.exists(cert_path)}")
    print(f"- Llave existe: {os.path.exists(key_path)}")
    
    # Verificar permisos
    print("\nPermisos de archivos:")
    cert_perms = oct(os.stat(cert_path).st_mode)[-3:]
    key_perms = oct(os.stat(key_path).st_mode)[-3:]
    print(f"- Permisos certificado: {cert_perms}")
    print(f"- Permisos llave: {key_perms}")
    
    # Verificar contenido
    print("\nContenido del certificado:")
    with open(cert_path, 'r') as f:
        cert_content = f.read()
        print("- Tiene BEGIN marker:", "-----BEGIN CERTIFICATE-----" in cert_content)
        print("- Tiene END marker:", "-----END CERTIFICATE-----" in cert_content)
        print("- Longitud:", len(cert_content))
    
    print("\nContenido de la llave:")
    with open(key_path, 'r') as f:
        key_content = f.read()
        print("- Tiene BEGIN marker:", "-----BEGIN PRIVATE KEY-----" in key_content)
        print("- Tiene END marker:", "-----END PRIVATE KEY-----" in key_content)
        print("- Longitud:", len(key_content))

if __name__ == "__main__":
    print("\nPrueba de carga de certificados")
    print("=" * 60)
    asyncio.run(test_certificates()) 
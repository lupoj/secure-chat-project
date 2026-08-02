from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import datetime

# Generate a private key and a self-signed certificate for the server
priv_key = rsa.generate_private_key(public_exponent = 65537, key_size = 2048)

# Define the subject and issuer for the certificate, using "localhost" as the common name
subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),])

# Build the certificate format with the specified subject, issuer, public key, serial number, validity period, and sign it with the private key using SHA256
certificate = (
    x509.CertificateBuilder()
    .subject_name(subject)
    .issuer_name(issuer)
    .public_key(priv_key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
    .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365))
    .sign(priv_key, hashes.SHA256())
)

# Write the private key and certificate to files in PEM format, without encryption for the private key
with open("server.key", "wb") as f:
    f.write(priv_key.private_bytes(
        encoding = serialization.Encoding.PEM,
        format = serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm = serialization.NoEncryption()
    ))

# Write the certificate to a file in PEM format
with open("server.crt", "wb") as f:
    f.write(certificate.public_bytes(serialization.Encoding.PEM))

print("server.key and server.crt have been generated successfully.")
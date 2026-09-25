#!/usr/bin/env bash
# Génère la PKI de cours (Module 5.2) : CA + cert serveur + cert client Envoy.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CERTS="$ROOT/certs"
mkdir -p "$CERTS"
cd "$CERTS"

# 1. Autorité de certification locale
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout ca.key -out ca.crt -days 3650 \
  -subj "/CN=Course CA" 2>/dev/null

# 2. Certificat du SERVEUR Python (SAN = chat-server)
openssl req -newkey rsa:4096 -nodes \
  -keyout server.key -out server.csr \
  -subj "/CN=chat-server" 2>/dev/null
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -days 365 \
  -out server.crt -extfile <(echo "subjectAltName=DNS:chat-server,DNS:localhost,IP:127.0.0.1") \
  2>/dev/null

# 3. Certificat du CLIENT Envoy
openssl req -newkey rsa:4096 -nodes \
  -keyout client.key -out client.csr \
  -subj "/CN=envoy-client" 2>/dev/null
openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -days 365 \
  -out client.crt 2>/dev/null

# 4. Certificat Nginx (TLS public pour le navigateur — auto-signé OK en cours)
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout nginx.key -out nginx.crt -days 365 \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1" 2>/dev/null

rm -f server.csr client.csr
# Envoy lit les clés en tant qu'utilisateur non-root : 644 requis en cours
chmod 644 *.key *.crt
echo "✅ Certificats générés dans $CERTS"
ls -1 "$CERTS"

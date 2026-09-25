"""Client de vérification Module 5 : mTLS + JWT + health + Login."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import grpc
from grpc_health.v1 import health_pb2, health_pb2_grpc

from generated import chat_pb2, chat_pb2_grpc

CERTS = Path(os.getenv("CERTS_DIR", "certs"))
TARGET = os.getenv("GRPC_TARGET", "localhost:50052")


def channel_mtls() -> grpc.Channel:
    with open(CERTS / "client.key", "rb") as f:
        private_key = f.read()
    with open(CERTS / "client.crt", "rb") as f:
        cert_chain = f.read()
    with open(CERTS / "ca.crt", "rb") as f:
        root_ca = f.read()
    creds = grpc.ssl_channel_credentials(
        root_certificates=root_ca,
        private_key=private_key,
        certificate_chain=cert_chain,
    )
    return grpc.secure_channel(TARGET, creds)


def expect_mtls_rejection() -> None:
    """Exercice 1 : sans certificat client → échec de connexion."""
    print("--- Exercice 1 : rejet sans certificat client ---")
    with open(CERTS / "ca.crt", "rb") as f:
        root_ca = f.read()
    # TLS serveur seulement, PAS de cert client
    creds = grpc.ssl_channel_credentials(root_certificates=root_ca)
    try:
        with grpc.secure_channel(TARGET, creds) as ch:
            stub = chat_pb2_grpc.ChatServiceStub(ch)
            stub.Login(
                chat_pb2.LoginRequest(username="mounir", password="password"),
                timeout=3,
            )
        print("❌ ÉCHEC : l'appel sans cert client a réussi")
        sys.exit(1)
    except grpc.RpcError as err:
        # UNAVAILABLE / SSL souvent
        print(f"✅ Rejeté comme attendu : {err.code().name} — {err.details() or err}")


def main() -> None:
    if not (CERTS / "ca.crt").exists():
        print("Générez les certificats : bash scripts/generate-certs.sh")
        sys.exit(1)

    expect_mtls_rejection()

    print("\n--- mTLS OK + health + Login + SendMessage ---")
    with channel_mtls() as channel:
        health = health_pb2_grpc.HealthStub(channel)
        status = health.Check(health_pb2.HealthCheckRequest(), timeout=3)
        print(f"Health : {health_pb2.HealthCheckResponse.ServingStatus.Name(status.status)}")

        stub = chat_pb2_grpc.ChatServiceStub(channel)

        # Sans JWT → UNAUTHENTICATED
        try:
            stub.SendMessage(
                chat_pb2.ChatMessage(user="mounir", text="hack", timestamp="t"),
                timeout=3,
            )
            print("❌ SendMessage sans JWT a réussi")
            sys.exit(1)
        except grpc.RpcError as err:
            print(f"✅ Sans JWT : {err.code().name} — {err.details()}")

        login = stub.Login(
            chat_pb2.LoginRequest(username="mounir", password="password"),
            timeout=3,
        )
        print(f"Login OK : user={login.user}, token={login.token[:24]}…")

        meta = (("authorization", f"Bearer {login.token}"),)
        ack = stub.SendMessage(
            chat_pb2.ChatMessage(
                user="mounir",
                text="Hello prod !",
                timestamp="2026-09-25T10:00:00",
            ),
            metadata=meta,
            timeout=3,
        )
        print(f"SendMessage OK : {ack.text}")

    print("\n✅ Module 5 (Python mTLS + JWT + health) : OK")


if __name__ == "__main__":
    main()

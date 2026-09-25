"""Assemblage du serveur gRPC de production (Module 5).

- TLS + mTLS (certs/)
- Health checks standards (grpc.health.v1)
- Intercepteurs : logging + JWT
"""

from __future__ import annotations

import os
from concurrent import futures
from pathlib import Path

import grpc
from grpc_health.v1 import health, health_pb2, health_pb2_grpc

from generated import chat_pb2_grpc
from interceptors import AuthInterceptor, LoggingInterceptor
from protos import user_pb2_grpc
from services import ChatService, UserService

CERTS_DIR = Path(os.getenv("CERTS_DIR", "certs"))
# GRPC_TLS=0 pour revenir au mode insecure des modules 1-4.
USE_TLS = os.getenv("GRPC_TLS", "1") != "0"
DEFAULT_PORT = int(os.getenv("GRPC_PORT", "50052" if USE_TLS else "50051"))


def _ssl_server_credentials() -> grpc.ServerCredentials:
    """Credentials serveur : TLS + exigence du certificat client (mTLS)."""
    with open(CERTS_DIR / "server.key", "rb") as f:
        private_key = f.read()
    with open(CERTS_DIR / "server.crt", "rb") as f:
        cert_chain = f.read()
    with open(CERTS_DIR / "ca.crt", "rb") as f:
        root_ca = f.read()
    return grpc.ssl_server_credentials(
        private_key_certificate_chain_pairs=[(private_key, cert_chain)],
        root_certificates=root_ca,
        require_client_auth=True,
    )


def serve(port: int | None = None) -> None:
    port = DEFAULT_PORT if port is None else port
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        interceptors=[LoggingInterceptor(), AuthInterceptor()],
    )

    # Health check standard (5.4) — PUBLIC (AuthInterceptor le laisse passer)
    health_servicer = health.HealthServicer()
    health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)
    health_servicer.set("", health_pb2.HealthCheckResponse.SERVING)
    health_servicer.set("chat.v1.ChatService", health_pb2.HealthCheckResponse.SERVING)

    user_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)
    chat_pb2_grpc.add_ChatServiceServicer_to_server(ChatService(), server)

    if USE_TLS:
        if not (CERTS_DIR / "server.crt").exists():
            raise FileNotFoundError(
                f"Certificats introuvables dans {CERTS_DIR}/ — "
                "lancez scripts/generate-certs.sh"
            )
        server.add_secure_port(f"[::]:{port}", _ssl_server_credentials())
        print(f"✅ Serveur gRPC sécurisé (TLS + mTLS) sur :{port}", flush=True)
    else:
        server.add_insecure_port(f"[::]:{port}")
        print(f"✅ Serveur gRPC insecure sur :{port} (GRPC_TLS=0)", flush=True)

    server.start()
    server.wait_for_termination()


def main() -> None:
    serve()


if __name__ == "__main__":
    main()

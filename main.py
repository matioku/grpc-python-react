"""Assemblage du serveur gRPC : servicers + intercepteurs + port (Module 2.7)."""

from concurrent import futures

import grpc

from generated import chat_pb2_grpc
from interceptors import AuthInterceptor, LoggingInterceptor
from protos import user_pb2_grpc
from services import ChatService, UserService


def serve(port: int = 50051) -> None:
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        # L'ordre compte : on logue tout, puis on filtre sur le jeton (4.5).
        interceptors=[LoggingInterceptor(), AuthInterceptor()],
    )
    user_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)
    chat_pb2_grpc.add_ChatServiceServicer_to_server(ChatService(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"✅ Serveur gRPC (User + Chat) sur le port {port}", flush=True)
    server.wait_for_termination()


def main() -> None:
    serve()


if __name__ == "__main__":
    main()

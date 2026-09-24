"""Logique métier UserService (Module 1, structurée pour le Module 2.7)."""

from __future__ import annotations

import grpc

from protos import user_pb2, user_pb2_grpc

FAKE_DB = {
    1: user_pb2.User(
        id=1,
        name="Mounir",
        email="mounir@example.com",
        nickname="mou",
        address=user_pb2.Address(street="12 rue de la Paix", city="Paris"),
    ),
    2: user_pb2.User(
        id=2,
        name="Alice",
        email="alice@example.com",
        nickname="ally",
        address={"street": "5 avenue des Champs", "city": "Lyon"},
    ),
}


class UserService(user_pb2_grpc.UserServiceServicer):
    """Servicer User — chaque RPC du .proto est implémentée ici."""

    def GetUser(self, request, context):
        user = FAKE_DB.get(request.user_id)
        if user is None:
            context.abort(
                grpc.StatusCode.NOT_FOUND,
                f"User {request.user_id} introuvable",
            )
        return user_pb2.GetUserResponse(user=user)

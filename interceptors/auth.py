"""Intercepteur JWT automatique (Module 5.3 — exercice 2).

Refuse tout appel non authentifié, sauf :
- health check gRPC standard
- Login (délivrance du jeton)
"""

from __future__ import annotations

import grpc

from auth.jwt_utils import check_jwt

from .handlers import Behavior, rebuild_handler

# Méthodes publiques (pas de Bearer requis).
_PUBLIC_SUFFIXES = (
    "/grpc.health.v1.Health/Check",
    "/grpc.health.v1.Health/Watch",
    "/chat.v1.ChatService/Login",
)


class AuthInterceptor(grpc.ServerInterceptor):
    """Vérifie le JWT avant d'appeler le servicer."""

    def intercept_service(self, continuation, handler_call_details):
        method = handler_call_details.method or ""
        handler = continuation(handler_call_details)
        if handler is None:
            return None

        if any(suffix in method for suffix in _PUBLIC_SUFFIXES):
            return handler

        def require_jwt(behavior: Behavior) -> Behavior:
            def wrapped(request_or_iterator, context):
                # Pose l'identité dans le contexte pour les servicers (optionnel).
                user = check_jwt(context)
                context.peer_identity_key = "jwt"  # type: ignore[attr-defined]
                context._jwt_user = user  # type: ignore[attr-defined]
                return behavior(request_or_iterator, context)

            return wrapped

        return rebuild_handler(handler, require_jwt)

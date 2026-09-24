"""Intercepteur d'authentification par metadata (Module 4.5).

Les metadata sont les « headers » de gRPC : elles voyagent À CÔTÉ de la
requête et ne font pas partie du contrat .proto. `authorization` est l'endroit
conventionnel pour le jeton — et l'intercepteur le bon endroit pour le
vérifier, plutôt que de répéter le test dans chaque méthode du servicer.

Désactivé par défaut pour ne pas casser les modules précédents : il ne
s'active que si la variable d'environnement CHAT_AUTH_TOKEN est définie.

    CHAT_AUTH_TOKEN=secret-token uv run python main.py

Le Module 5 en fera un vrai système (rôles, expiration, TLS).
"""

from __future__ import annotations

import os

import grpc

from .handlers import Behavior, metadata_dict, rebuild_handler


class AuthInterceptor(grpc.ServerInterceptor):
    """Exige `authorization: Bearer <jeton>` quand un jeton est configuré."""

    def __init__(self, token: str | None = None) -> None:
        self._token = token if token is not None else os.getenv("CHAT_AUTH_TOKEN", "")

    def intercept_service(self, continuation, handler_call_details):
        handler = continuation(handler_call_details)
        # Pas de jeton configuré → serveur ouvert (comportement des modules 1-3)
        if handler is None or not self._token:
            return handler

        auth = metadata_dict(handler_call_details).get("authorization", "")
        if auth == f"Bearer {self._token}":
            return handler

        details = "Jeton absent" if not auth else "Jeton invalide"

        def deny(_behavior: Behavior) -> Behavior:
            def terminate(request_or_iterator, context):
                # abort() lève une exception : la méthode du servicer n'est
                # JAMAIS appelée. Le client reçoit UNAUTHENTICATED (code 16).
                context.abort(grpc.StatusCode.UNAUTHENTICATED, details)

            return terminate

        # On garde le type du handler (unary/stream) : c'est lui qui pilote la
        # (dé)sérialisation, même pour renvoyer une erreur.
        return rebuild_handler(handler, deny)

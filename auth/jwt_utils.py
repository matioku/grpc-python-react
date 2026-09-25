"""Authentification JWT (Module 5.3) + helpers partagés."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import grpc
import jwt

# En vrai : variable d'environnement, jamais en dur dans le code (checklist 5.6).
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-prod-please-use-32b+")
JWT_ALGORITHM = "HS256"
JWT_TTL_MINUTES = int(os.getenv("JWT_TTL_MINUTES", "60"))

# Comptes de démo du cours (exercice 3).
DEMO_USERS = {
    "mounir": "password",
    "alice": "password",
    "bob": "password",
}


def issue_token(username: str) -> str:
    """Signe un JWT court (sub = username)."""
    now = datetime.now(UTC)
    payload = {
        "sub": username,
        "iat": now,
        "exp": now + timedelta(minutes=JWT_TTL_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def check_jwt(context: grpc.ServicerContext) -> str:
    """Extrait et valide le jeton depuis les metadata.

    Renvoie le nom d'utilisateur (`sub`), ou abort UNAUTHENTICATED.
    """
    metadata = dict(context.invocation_metadata() or ())
    raw = metadata.get("authorization", "")
    token = raw.removeprefix("Bearer ").strip()
    if not token:
        context.abort(grpc.StatusCode.UNAUTHENTICATED, "Jeton absent")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        sub = payload.get("sub")
        if not sub:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Jeton invalide ou expiré")
        return str(sub)
    except jwt.PyJWTError:
        context.abort(grpc.StatusCode.UNAUTHENTICATED, "Jeton invalide ou expiré")

"""Outil partagé par les intercepteurs (Module 4).

Un intercepteur ne peut pas « modifier » un handler gRPC : il doit en
reconstruire un du MÊME type (unary_unary, unary_stream, stream_unary,
stream_stream) autour d'un nouveau comportement. Ce module factorise cette
gymnastique pour que LoggingInterceptor et AuthInterceptor restent lisibles.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import grpc

# Un « behavior » = la méthode du servicer (request_or_iterator, context) -> réponse
Behavior = Callable[..., Any]


def rebuild_handler(
    handler: grpc.RpcMethodHandler,
    wrap: Callable[[Behavior], Behavior],
) -> grpc.RpcMethodHandler:
    """Renvoie le même handler, comportement remplacé par `wrap(behavior)`.

    L'arité (streaming ou non, en entrée comme en sortie) est préservée : c'est
    elle qui dit à gRPC comment lire la requête et écrire la réponse.
    """
    if handler.request_streaming and handler.response_streaming:
        behavior, factory = handler.stream_stream, grpc.stream_stream_rpc_method_handler
    elif handler.request_streaming:
        behavior, factory = handler.stream_unary, grpc.stream_unary_rpc_method_handler
    elif handler.response_streaming:
        behavior, factory = handler.unary_stream, grpc.unary_stream_rpc_method_handler
    else:
        behavior, factory = handler.unary_unary, grpc.unary_unary_rpc_method_handler

    return factory(
        wrap(behavior),
        request_deserializer=handler.request_deserializer,
        response_serializer=handler.response_serializer,
    )


def metadata_dict(handler_call_details: grpc.HandlerCallDetails) -> dict[str, str]:
    """Metadata de l'appel sous forme de dictionnaire.

    ⚠ Piège classique : `invocation_metadata` est un TUPLE de paires
    (clé, valeur), pas un dict — il n'a donc pas de `.get()`. Les clés sont
    toujours en minuscules (règle HTTP/2).
    """
    return dict(handler_call_details.invocation_metadata or ())

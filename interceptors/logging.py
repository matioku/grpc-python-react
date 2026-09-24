"""Intercepteur de logging — middleware gRPC (Module 2.6)."""

from __future__ import annotations

import time
from collections.abc import Callable, Iterator
from typing import Any

import grpc


class LoggingInterceptor(grpc.ServerInterceptor):
    """Logue chaque RPC avec sa durée, pour unary et streaming."""

    def intercept_service(self, continuation, handler_call_details):
        method = handler_call_details.method
        handler = continuation(handler_call_details)
        if handler is None:
            return None

        def wrap(behavior: Callable[..., Any]) -> Callable[..., Any]:
            def new_behavior(request_or_iterator, context):
                start = time.time()

                def _log() -> None:
                    elapsed_ms = (time.time() - start) * 1000
                    print(f"📥 {method} — {elapsed_ms:.0f} ms")

                try:
                    result = behavior(request_or_iterator, context)
                except Exception:
                    _log()
                    raise

                # Streaming réponse : générateur — logger à la fin du flux
                if hasattr(result, "__iter__") and not isinstance(
                    result, (bytes, str, dict, list, tuple)
                ):

                    def logged_stream() -> Iterator:
                        try:
                            yield from result
                        finally:
                            _log()

                    return logged_stream()

                _log()
                return result

            return new_behavior

        if handler.request_streaming and handler.response_streaming:
            return grpc.stream_stream_rpc_method_handler(
                wrap(handler.stream_stream),
                request_deserializer=handler.request_deserializer,
                response_serializer=handler.response_serializer,
            )
        if handler.request_streaming:
            return grpc.stream_unary_rpc_method_handler(
                wrap(handler.stream_unary),
                request_deserializer=handler.request_deserializer,
                response_serializer=handler.response_serializer,
            )
        if handler.response_streaming:
            return grpc.unary_stream_rpc_method_handler(
                wrap(handler.unary_stream),
                request_deserializer=handler.request_deserializer,
                response_serializer=handler.response_serializer,
            )
        return grpc.unary_unary_rpc_method_handler(
            wrap(handler.unary_unary),
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )

"""Logique métier ChatService — 4 types d'appels gRPC + exercices Module 2."""

from __future__ import annotations

import queue
import threading
from itertools import count

import grpc

from generated import chat_pb2, chat_pb2_grpc

# ---- État partagé du serveur (en mémoire pour le cours) ----
MESSAGES: list[chat_pb2.ChatMessage] = []
SUBSCRIBERS: list[queue.Queue] = []
_NEXT_ID = count(1)


def _assign_id(msg: chat_pb2.ChatMessage) -> chat_pb2.ChatMessage:
    """Attribue un id unique si le message n'en a pas encore."""
    if msg.id == 0:
        msg = chat_pb2.ChatMessage(
            id=next(_NEXT_ID),
            user=msg.user,
            text=msg.text,
            timestamp=msg.timestamp,
        )
    return msg


def _broadcast(msg: chat_pb2.ChatMessage) -> None:
    """Pousse un message vers TOUS les abonnés (Chat bidi + Subscribe grpc-web)."""
    for subscriber in list(SUBSCRIBERS):
        subscriber.put(msg)


class ChatService(chat_pb2_grpc.ChatServiceServicer):
    # ================= 1. UNARY =================
    def SendMessage(self, request, context):
        """1 requête → 1 réponse. Validation via status codes (2.5)."""
        # Module 4.5 — invocation_metadata() renvoie un TUPLE de paires
        # (clé, valeur) : pas de .get() dessus, il faut passer par dict().
        request_id = dict(context.invocation_metadata()).get("x-request-id")
        if request_id:
            # On le renvoie au client pour qu'il puisse corréler ses logs
            context.send_initial_metadata((("x-request-id", request_id),))

        if not request.text.strip():
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "Le message est vide",
            )
        if request.timestamp == "":
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "Timestamp requis",
            )

        stored = _assign_id(request)
        MESSAGES.append(stored)
        # Module 4 : le navigateur ne peut pas ouvrir de flux montant. Son
        # "envoi" est cet appel unary — c'est donc ici qu'on diffuse aux abonnés.
        _broadcast(stored)
        return chat_pb2.ChatMessage(
            id=stored.id,
            user=stored.user,
            text=f"✅ Reçu par le serveur : {stored.text}",
            timestamp=stored.timestamp,
        )

    # ================= 2. SERVER STREAMING =================
    def History(self, request, context):
        """Yield les messages filtrés (N derniers si limit > 0)."""
        user_msgs = [msg for msg in MESSAGES if msg.user == request.user]
        if request.limit > 0:
            user_msgs = user_msgs[-request.limit :]
        for msg in user_msgs:
            # Module 4.4 — on respecte le client au lieu de streamer dans le vide.
            if not context.is_active():
                return  # onglet fermé / stream.cancel() : inutile de continuer
            remaining = context.time_remaining()  # None = appel SANS deadline
            if remaining is not None and remaining < 0.1:
                # Mieux vaut un statut explicite qu'un flux tronqué en silence
                context.abort(
                    grpc.StatusCode.DEADLINE_EXCEEDED,
                    "Historique interrompu : plus assez de temps",
                )
            yield msg

    # ================= 3. CLIENT STREAMING =================
    def UploadBatch(self, request_iterator, context):
        """Le client envoie plusieurs SubscribeRequest ; une seule réponse."""
        count_msgs = 0
        for req in request_iterator:
            for msg in req.messages:
                MESSAGES.append(_assign_id(msg))
                count_msgs += 1
        return chat_pb2.UploadSummary(count=count_msgs)

    # ================= 4. BIDIRECTIONNEL =================
    def Chat(self, request_iterator, context):
        """Queue + thread + broadcast — pattern chat temps réel."""
        my_queue: queue.Queue = queue.Queue()
        SUBSCRIBERS.append(my_queue)

        def reader() -> None:
            try:
                for msg in request_iterator:
                    stored = _assign_id(msg)
                    MESSAGES.append(stored)
                    _broadcast(stored)
            except grpc.RpcError:
                # Client a fermé le flux — normal en fin de session
                pass
            finally:
                if my_queue in SUBSCRIBERS:
                    SUBSCRIBERS.remove(my_queue)

        threading.Thread(target=reader, daemon=True).start()

        while context.is_active():
            try:
                msg = my_queue.get(timeout=1)
                yield msg
            except queue.Empty:
                continue

    # ========= 5. SERVER STREAMING temps réel — Module 4 (grpc-web) =========
    def Subscribe(self, request, context):
        """Flux DESCENDANT du chat, la moitié « lecture » de Chat.

        Le navigateur ne peut pas ouvrir de flux montant (limite grpc-web) :
        il s'abonne ici une fois pour toutes et envoie via SendMessage.
        Même liste SUBSCRIBERS que Chat : navigateurs et clients Python
        se parlent entre eux.
        """
        my_queue: queue.Queue = queue.Queue()
        SUBSCRIBERS.append(my_queue)
        who = request.user or "anonyme"
        print(f"🔌 {who} s'abonne — {len(SUBSCRIBERS)} abonné(s)", flush=True)
        try:
            # Pas de deadline sur ce flux : il doit vivre tant que l'onglet est
            # ouvert. Le timeout de la queue sert juste à revérifier is_active().
            while context.is_active():
                try:
                    msg = my_queue.get(timeout=1)
                except queue.Empty:
                    continue
                yield msg
        finally:
            # Déconnexion (onglet fermé, stream.cancel()) : on libère la queue,
            # sinon le serveur pousse des messages dans le vide indéfiniment.
            if my_queue in SUBSCRIBERS:
                SUBSCRIBERS.remove(my_queue)
            print(f"🔌 {who} s'est déconnecté — {len(SUBSCRIBERS)} abonné(s)", flush=True)

    # ================= Exercice 1 : DeleteMessage =================
    def DeleteMessage(self, request, context):
        """Supprime un message par id ; NOT_FOUND s'il n'existe pas."""
        for i, msg in enumerate(MESSAGES):
            if msg.id == request.id:
                del MESSAGES[i]
                return chat_pb2.UploadSummary(count=1)
        context.abort(
            grpc.StatusCode.NOT_FOUND,
            f"Message {request.id} introuvable",
        )

"""Client de test : 4 types d'appels (2.4/2.8) + deadlines & metadata (4.4/4.5)."""

from __future__ import annotations

import threading
import time

import grpc

from generated import chat_pb2, chat_pb2_grpc


def demo_unary(stub: chat_pb2_grpc.ChatServiceStub) -> chat_pb2.ChatMessage:
    ack = stub.SendMessage(
        chat_pb2.ChatMessage(
            user="Mounir",
            text="Bonjour le chat !",
            timestamp="2026-09-22T10:00:00",
        )
    )
    print("Unary :", ack.text, f"(id={ack.id})")
    return ack


def demo_unary_errors(stub: chat_pb2_grpc.ChatServiceStub) -> None:
    try:
        stub.SendMessage(chat_pb2.ChatMessage(user="Mounir", text=""))
    except grpc.RpcError as err:
        print(f"Erreur gRPC : {err.code().name} — {err.details()}")


def demo_history(stub: chat_pb2_grpc.ChatServiceStub, limit: int = 0) -> None:
    print(f"\nHistorique de Mounir (limit={limit or 'tous'}) :")
    for msg in stub.History(chat_pb2.HistoryRequest(user="Mounir", limit=limit)):
        print(f"  [{msg.timestamp}] #{msg.id} {msg.user}: {msg.text}")


def demo_client_streaming(stub: chat_pb2_grpc.ChatServiceStub) -> None:
    def batch():
        yield chat_pb2.SubscribeRequest(
            user="Mounir",
            messages=[
                chat_pb2.ChatMessage(user="Mounir", text="msg 1", timestamp="t1"),
                chat_pb2.ChatMessage(user="Mounir", text="msg 2", timestamp="t2"),
            ],
        )
        yield chat_pb2.SubscribeRequest(
            user="Alice",
            messages=[
                chat_pb2.ChatMessage(user="Alice", text="msg 3", timestamp="t3"),
            ],
        )

    summary = stub.UploadBatch(batch())
    print("\nClient streaming :", summary.count, "messages reçus")


def demo_delete(stub: chat_pb2_grpc.ChatServiceStub, msg_id: int) -> None:
    try:
        summary = stub.DeleteMessage(chat_pb2.MessageId(id=msg_id))
        print(f"\nDeleteMessage #{msg_id} : {summary.count} supprimé(s)")
    except grpc.RpcError as err:
        print(f"\nDeleteMessage #{msg_id} → {err.code().name} : {err.details()}")


def demo_deadline(stub: chat_pb2_grpc.ChatServiceStub) -> None:
    """Module 4.4 : borner l'attente au lieu de rester suspendu."""
    print("\n--- Deadlines ---")
    ack = stub.SendMessage(
        chat_pb2.ChatMessage(user="Mounir", text="ping", timestamp="t-deadline"),
        timeout=2.0,  # 2 s max, sinon DEADLINE_EXCEEDED
    )
    print("  SendMessage (deadline 2 s) :", ack.text)

    # Subscribe est un flux SANS fin : sans deadline, cette boucle ne rendrait
    # jamais la main. Avec un deadline, gRPC coupe et lève l'erreur.
    start = time.time()
    try:
        for _ in stub.Subscribe(chat_pb2.SubscribeRequest(user="Mounir"), timeout=1.0):
            pass
    except grpc.RpcError as err:
        elapsed = time.time() - start
        print(f"  Subscribe (deadline 1 s) → {err.code().name} après {elapsed:.1f} s")


def demo_metadata(stub: chat_pb2_grpc.ChatServiceStub) -> None:
    """Module 4.5 : les « headers » de gRPC, hors contrat .proto."""
    print("\n--- Metadata ---")
    metadata = (
        ("x-request-id", "demo-42"),
        ("x-client-app", "chat_client.py"),
        ("authorization", "Bearer secret-token"),
    )
    ack, call = stub.SendMessage.with_call(
        chat_pb2.ChatMessage(user="Mounir", text="avec metadata", timestamp="t-meta"),
        metadata=metadata,
        timeout=2.0,
    )
    print("  Envoyées → le serveur les logue :", dict(metadata[:2]))
    print("  Reçues   ← metadata initiales du serveur :", dict(call.initial_metadata()))
    print("  Réponse  :", ack.text)


def demo_subscribe_broadcast() -> None:
    """Module 4 : le duo du navigateur — Subscribe (descendant) + SendMessage (montant)."""
    print("\n--- Subscribe + SendMessage (ce que fait React) ---")
    received: list[str] = []
    ready = threading.Event()

    def listener() -> None:
        with grpc.insecure_channel("localhost:50051") as channel:
            stub = chat_pb2_grpc.ChatServiceStub(channel)
            stream = stub.Subscribe(
                chat_pb2.SubscribeRequest(user="Navigateur"),
                timeout=5.0,
            )
            ready.set()
            try:
                for msg in stream:
                    received.append(f"{msg.user}: {msg.text}")
                    break  # un seul message suffit pour la démo
            except grpc.RpcError as err:
                print(f"  Flux interrompu : {err.code().name}")

    thread = threading.Thread(target=listener)
    thread.start()
    ready.wait(timeout=2)
    time.sleep(0.3)  # laisse le serveur enregistrer l'abonnement

    with grpc.insecure_channel("localhost:50051") as channel:
        stub = chat_pb2_grpc.ChatServiceStub(channel)
        stub.SendMessage(
            chat_pb2.ChatMessage(user="Alice", text="Coucou les abonnés !", timestamp="t-sub"),
            timeout=2.0,
        )

    thread.join(timeout=5)
    print("  L'abonné a reçu :", received)


def demo_bidi_two_clients() -> None:
    """Exercice 3 : deux clients bidirectionnels en parallèle."""
    print("\n--- Chat bidirectionnel (2 clients) ---")
    barrier = threading.Barrier(2)
    received: dict[str, list[str]] = {"Alice": [], "Bob": []}

    def run_client(name: str, peer_text: str) -> None:
        with grpc.insecure_channel("localhost:50051") as channel:
            stub = chat_pb2_grpc.ChatServiceStub(channel)

            def outgoing():
                barrier.wait()
                yield chat_pb2.ChatMessage(
                    user=name,
                    text=peer_text,
                    timestamp="2026-09-22T12:00:00",
                )
                # Laisse le temps de recevoir le message de l'autre
                time.sleep(1.5)

            responses = stub.Chat(outgoing())
            deadline = time.time() + 3
            for msg in responses:
                if msg.user != name:
                    received[name].append(f"{msg.user}: {msg.text}")
                    print(f"  [{name} reçoit] {msg.user}: {msg.text}")
                if time.time() > deadline or len(received[name]) >= 1:
                    break

    t1 = threading.Thread(target=run_client, args=("Alice", "Salut Bob !"))
    t2 = threading.Thread(target=run_client, args=("Bob", "Hello Alice !"))
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    print(f"  Alice a reçu : {received['Alice']}")
    print(f"  Bob a reçu   : {received['Bob']}")


def main() -> None:
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = chat_pb2_grpc.ChatServiceStub(channel)

        ack = demo_unary(stub)
        demo_unary_errors(stub)
        demo_client_streaming(stub)
        demo_history(stub, limit=0)
        demo_history(stub, limit=2)
        demo_delete(stub, ack.id)
        demo_delete(stub, 999_999)  # NOT_FOUND attendu
        demo_deadline(stub)
        demo_metadata(stub)

    demo_bidi_two_clients()
    demo_subscribe_broadcast()


if __name__ == "__main__":
    main()

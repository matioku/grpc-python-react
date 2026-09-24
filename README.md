# gRPC Python

## Initialisation

```bash
uv sync
```

## Générer les classes depuis le .proto

À relancer après **chaque** modification de `protos/user.proto` :

```bash
uv run python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. protos/user.proto
```

Produit `protos/user_pb2.py`, `protos/user_pb2.pyi`, `protos/user_pb2_grpc.py` (non versionnés).

> Le `-I.` est obligatoire : protoc écrit l'import Python à partir du chemin du `.proto`
> relatif au `-I`. Avec `-Iprotos` il génère `import user_pb2` au lieu de
> `from protos import user_pb2` → `ModuleNotFoundError`.

## Lancer

```bash
uv run python server.py   # terminal 1
uv run python client.py   # terminal 2
```

> Tuer l'ancien serveur avant d'en relancer un (`pkill -f server.py`) : gRPC active
> `SO_REUSEPORT`, deux serveurs peuvent écouter sur 50051 sans erreur et se partager
> les requêtes.

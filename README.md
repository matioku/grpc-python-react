# gRPC Python + React — Module 2

## Initialisation

```bash
uv sync
```

## Générer les classes depuis les .proto

À relancer après **chaque** modification d'un fichier dans `protos/` :

```bash
# User (Module 1) → protos/
uv run python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. protos/user.proto

# Chat (Module 2) → generated/
uv run python -m grpc_tools.protoc \
  -Iprotos \
  --python_out=generated \
  --pyi_out=generated \
  --grpc_python_out=generated \
  chat.proto

# Corrige l'import pour le package `generated`
sed -i 's/^import chat_pb2/from generated import chat_pb2/' generated/chat_pb2_grpc.py
```

> User : le `-I.` est obligatoire pour obtenir `from protos import user_pb2`.
> Chat : sortie dans `generated/` comme demandé au Module 2 ; le `sed` aligne l'import gRPC.

## Structure (Module 2.7)

```
├── protos/           # contrats .proto
├── generated/        # stubs Chat (régénérés, non versionnés)
├── services/         # logique métier (UserService, ChatService)
├── interceptors/     # LoggingInterceptor
├── main.py           # assemblage serveur + servicers + intercepteurs
├── chat_client.py    # tests des 4 types + exercices
└── client.py         # client User (Module 1)
```

## Lancer

```bash
uv run python main.py         # terminal 1 — User + Chat sur :50051
uv run python chat_client.py  # terminal 2 — démo Chat
uv run python client.py       # optionnel — démo User
```

> Tuer l'ancien serveur avant d'en relancer un (`pkill -f 'main.py|server.py'`).

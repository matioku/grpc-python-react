# gRPC Python + React — Modules 2 & 3

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

# Corrige l'import pour le package `generated` (macOS : sed -i '' ...)
sed -i 's/^import chat_pb2/from generated import chat_pb2/' generated/chat_pb2_grpc.py
```

> User : le `-I.` est obligatoire pour obtenir `from protos import user_pb2`.
> Chat : sortie dans `generated/` comme demandé au Module 2 ; le `sed` aligne l'import gRPC.

## Structure (Module 2.7 + Module 3)

```
├── protos/           # contrats .proto (partagés Python ⇄ TypeScript)
├── generated/        # stubs Chat Python (régénérés, non versionnés)
├── services/         # logique métier (UserService, ChatService)
├── interceptors/     # LoggingInterceptor
├── main.py           # assemblage serveur + servicers + intercepteurs
├── chat_client.py    # tests des 4 types + exercices
├── client.py         # client User (Module 1)
├── envoy.yaml        # proxy grpc-web → gRPC (Module 3.4)
└── frontend/         # React + Vite + TypeScript (Module 3)
    └── src/
        ├── generated/    # stubs grpc-web (npm run proto) — seul package.json est versionné
        ├── grpc/client.ts
        ├── components/   # SendMessage (unary), History (server streaming)
        └── App.tsx
```

## Lancer (Module 2)

```bash
uv run python main.py         # terminal 1 — User + Chat sur :50051
uv run python chat_client.py  # terminal 2 — démo Chat
uv run python client.py       # optionnel — démo User
```

> Tuer l'ancien serveur avant d'en relancer un (`pkill -f 'main.py|server.py'`).

## Frontend React (Module 3)

Le navigateur ne parle pas gRPC natif (HTTP/2 brut) : il parle **grpc-web**, et le proxy **Envoy** traduit vers le serveur Python, qui ne change pas.

```
React :5173 ──grpc-web (HTTP/1.1)──▶ Envoy :8080 ──gRPC (HTTP/2)──▶ main.py :50051
```

### Prérequis (une fois)

```bash
brew install protobuf protoc-gen-grpc-web protoc-gen-js   # protoc + plugins grpc-web et JS
# + Docker (pour Envoy) et Node.js
```

### Installer et générer le client TypeScript

```bash
cd frontend
npm install
npm run proto   # protoc → src/generated/{chat_pb.js, chat_pb.d.ts, ChatServiceClientPb.ts}
```

`npm run dev` et `npm run build` relancent `npm run proto` automatiquement (`predev` / `prebuild`) : le front reste synchronisé avec `protos/chat.proto`.

### Lancement complet (3 terminaux)

```bash
# Terminal 1 — le serveur Python (Module 2)
uv run python main.py

# Terminal 2 — le proxy Envoy
docker run --rm -it -v "$(pwd)/envoy.yaml:/etc/envoy/envoy.yaml:ro" \
  -p 8080:8080 -p 9901:9901 envoyproxy/envoy:v1.39-latest

# Terminal 3 — le front React
cd frontend && npm run dev
# → http://localhost:5173
```

> **Port 8080 déjà pris ?** Publier Envoy ailleurs (`-p 18080:8080`) et lancer le front avec
> `VITE_GRPC_URL=http://localhost:18080 npm run dev`.
> **Linux** : ajouter `--add-host=host.docker.internal:host-gateway` au `docker run`.

Vérifications utiles : `curl -s localhost:9901/clusters | grep health_flags` (le cluster `chat_service` doit être `healthy`).

### Exercices

1. `History` affiche l'auteur (`getUser()`) : `[timestamp] Mounir : texte`.
2. Bouton **Actualiser** : `stream.cancel()` sur l'ancien flux puis ré-ouverture (clé `refreshKey` du `useEffect`).
3. Envoyer un message vide → le serveur répond `INVALID_ARGUMENT`, affiché en rouge : `INVALID_ARGUMENT (3) : Le message est vide`.

### Écarts avec le PDF du Module 3 (sinon ça ne fonctionne pas)

| PDF | Ici | Pourquoi |
|---|---|---|
| `npm install @google-protobuf` | `google-protobuf` + `@types/google-protobuf` | `@google-protobuf` n'existe pas |
| `ts-protoc-gen` / `--plugin=protoc-gen-ts` | `protoc-gen-grpc-web` + `protoc-gen-js` (brew) | `--grpc-web_out` utilise `protoc-gen-grpc-web` ; `--js_out` n'est plus intégré à protoc |
| `mode=grpcweb` | `mode=grpcwebtext` | le mode binaire ne gère que l'unary → `History` (streaming) casserait |
| `Chat_pb` | `chat_pb` | nom réellement généré depuis `chat.proto` |
| `import … from "../generated/…"` | `import … from "generated/…"` | `chat_pb.js` est en CommonJS : `src/generated` est un paquet local (`file:`) pré-bundlé par Vite (`resolve.preserveSymlinks`) |
| `History(ChatMessage)` | `History(HistoryRequest)` | contrat du Module 2 de ce repo (user + limit) |
| Envoy : `api_type`, cluster `STATIC` | `"@type"`, cluster `LOGICAL_DNS` | syntaxe Envoy v3 ; STATIC n'accepte que des IP |
| Envoy sans CORS ni `timeout` | filtre `cors` + `timeout: 0s` | 5173 → 8080 est cross-origin ; timeout 15 s par défaut sur les streams |
| cluster → `:50052` | cluster → `:50051` | ici User + Chat tournent ensemble dans `main.py` |
| `envoyproxy/envoy-dev:latest` | `envoyproxy/envoy:v1.39-latest` | image stable plutôt que build de dev |

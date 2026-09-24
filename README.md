# gRPC Python + React — Modules 2, 3 & 4

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

## Structure (Module 2.7 + Modules 3 & 4)

```
├── protos/           # contrats .proto (partagés Python ⇄ TypeScript)
├── generated/        # stubs Chat Python (régénérés, non versionnés)
├── services/         # logique métier (UserService, ChatService)
├── interceptors/     # LoggingInterceptor (+ metadata), AuthInterceptor
├── main.py           # assemblage serveur + servicers + intercepteurs
├── chat_client.py    # tests des 4 types + deadlines + metadata
├── client.py         # client User (Module 1)
├── envoy.yaml        # proxy grpc-web → gRPC (Module 3.4)
└── frontend/         # React + Vite + TypeScript (Modules 3 & 4)
    └── src/
        ├── generated/    # stubs grpc-web (npm run proto) — seul package.json est versionné
        ├── grpc/         # client.ts, metadata.ts (deadline + headers), errors.ts
        ├── hooks/        # useChat.ts — toute la logique gRPC du chat
        ├── components/   # ChatRoom (temps réel), SendMessage (unary), History (streaming)
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

## Communication avancée (Module 4)

### Le chat temps réel dans le navigateur

```
                     Subscribe  (stream descendant, sans deadline)
  React ◀────────────────────────────────────── Envoy ◀──── Python
  React ──────────────────────────────────────▶ Envoy ────▶ Python
                     SendMessage (unary, deadline 5 s)
```

Le serveur diffuse (`_broadcast`) chaque message à **tous** les abonnés : navigateurs
(`Subscribe`) *et* clients Python (`Chat` bidirectionnel) partagent la même liste `SUBSCRIBERS`.
Un message envoyé depuis React arrive donc dans un client Python, et inversement.

Toute la logique gRPC est dans `frontend/src/hooks/useChat.ts` ; `ChatRoom.tsx` ne fait que
l'affichage (**hooks = gRPC, composants = UI**).

**Tester** : ouvrir deux onglets sur http://localhost:5173 avec deux pseudos différents.

### Deadlines (4.4)

| Où | Comment |
|---|---|
| Client Python | `stub.SendMessage(msg, timeout=2.0)` → `DEADLINE_EXCEEDED` |
| Client React | metadata `deadline` = **timestamp absolu en ms** (`String(Date.now() + 5000)`), voir `grpc/metadata.ts` |
| Serveur | `context.is_active()` et `context.time_remaining()` dans `History` |

> Règle de prod : un deadline sur tout appel borné (5 s par défaut ici) — **sauf** sur `Subscribe`,
> un flux qui doit vivre aussi longtemps que l'onglet.

### Metadata (4.5)

Envoyées par le front à chaque appel (`callMetadata()`) : `x-client-app`, `x-request-id`, et
`authorization` si `VITE_GRPC_TOKEN` est défini. Côté Python, elles sont lues **dans les
intercepteurs** (`interceptors/logging.py`, `interceptors/auth.py`), pas dans chaque méthode :

```
📥 /chat.v1.ChatService/SendMessage — 0 ms [client=react-web req-id=5f1c…]
```

Auth par jeton, désactivée par défaut (le Module 5 en fera un vrai système) :

```bash
CHAT_AUTH_TOKEN=secret-token uv run python main.py           # terminal 1
VITE_GRPC_TOKEN=secret-token npm run dev                     # terminal 3
# sans jeton → UNAUTHENTICATED (16) « Jeton absent »
```

### Erreurs (4.6)

`frontend/src/grpc/errors.ts` traduit le status code en message humain et dit si l'erreur est
**réessayable** (`UNAVAILABLE`, `DEADLINE_EXCEEDED`) ou **définitive** (`INVALID_ARGUMENT`,
`UNAUTHENTICATED`, `NOT_FOUND`) → bouton « Réessayer » affiché seulement dans le premier cas.

### Exercices

1. Le flux est gardé dans le `useEffect` de `useChat` (fermé par `stream.cancel()` au démontage) ;
   l'envoi passe par `send()`, sans recréer la connexion.
2. Metadata d'identification du client envoyée à chaque appel et loguée par l'intercepteur.
3. Bouton **Réessayer** sur les erreurs réessayables (`canRetry`/`retry` dans `useChat`).

### Écarts avec le PDF du Module 4 (sinon ça ne fonctionne pas)

| PDF | Ici | Pourquoi |
|---|---|---|
| `const stream = client.chat(hello, {})` puis `stream.write(msg)` | `client.subscribe(...)` (descendant) + `client.sendMessage(...)` (montant) | **grpc-web ne génère aucune méthode client/bidi streaming** : `ChatServiceClientPb.ts` ne contient ni `chat()` ni `uploadBatch()`, et `ClientReadableStream` n'a pas de `.write()`. Le `Chat` bidi reste utilisable par les clients natifs (Python) |
| message d'entrée `"__join__"` | `SubscribeRequest.user` | un message bidon serait diffusé à tout le monde |
| `import { ChatMessage } from "../generated/Chat_pb"` | `from "generated/chat_pb"` | mêmes raisons qu'au Module 3 |
| `client.sendMessage(request, {}, metadata)` (metadata en 3ᵉ argument) | `client.sendMessage(request, metadata)` | en grpc-web le 2ᵉ argument **est** la metadata ; le 3ᵉ est un callback |
| `{ deadline: Date.now() + 2000 }` présenté comme des « call options » | `metadata.deadline = String(Date.now() + 5000)` | `deadline` est une **clé de metadata** (chaîne) que grpc-web convertit en header `grpc-timeout` |
| `import { grpc } from "grpc-web"` | `import { StatusCode } from "grpc-web"` | il n'y a pas d'export `grpc` |
| `context.invocation_metadata().get("authorization")` | `dict(context.invocation_metadata()).get(...)` | `invocation_metadata()` renvoie un **tuple de paires**, sans `.get()` |
| `if context.time_remaining() < 0.1` | `remaining is not None and remaining < 0.1` | `time_remaining()` vaut `None` quand le client n'a pas posé de deadline → `TypeError` |
| metadata `x-user-agent: "react-web"` (exercice 2) | `x-client-app: "react-web"` | grpc-web écrase `x-user-agent` avec sa propre valeur juste avant l'envoi |
| CORS du Module 3 inchangé | `allow_headers` + `authorization,x-request-id,x-client-app` | toute metadata custom voyage en header HTTP : sans autorisation, le preflight bloque l'appel |
| flux tronqué en silence (`break`) quand le temps manque | `context.abort(DEADLINE_EXCEEDED, …)` | sinon le client reçoit un `OK` avec des données partielles |

> Le PDF numérote ce module « 4 » (le Module 3 étant le frontend React déjà présent dans ce repo).

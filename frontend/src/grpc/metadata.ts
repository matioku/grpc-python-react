import type { Metadata } from "grpc-web";

// Les METADATA sont les "headers" de gRPC (4.5) : des paires clé/valeur
// envoyées À CÔTÉ de la requête, hors du contrat .proto. En grpc-web, c'est
// le 2e argument de chaque appel — pas un objet d'options séparé.

/** Deadline par défaut des appels bornés (règle de prod du 4.4). */
export const DEFAULT_DEADLINE_MS = 5000;

/**
 * Metadata communes à tous les appels.
 *
 * @param deadlineMs durée max de l'appel ; `null` pour un flux sans fin
 *                   (Subscribe : un deadline couperait le chat).
 */
export function callMetadata(deadlineMs: number | null = DEFAULT_DEADLINE_MS): Metadata {
  const metadata: Metadata = {
    // Exercice 2 : le front s'annonce, l'intercepteur Python le logue.
    // ⚠ PAS "x-user-agent" : grpc-web écrase cette clé avec sa propre valeur
    //   ("grpc-web-javascript/0.1") juste avant l'envoi.
    "x-client-app": "react-web",
    // Corrélation des logs navigateur ⇄ serveur (le serveur nous le renvoie)
    "x-request-id": crypto.randomUUID(),
  };

  // Jeton d'auth facultatif : VITE_GRPC_TOKEN=secret-token npm run dev,
  // en face de CHAT_AUTH_TOKEN=secret-token uv run python main.py.
  const token = import.meta.env.VITE_GRPC_TOKEN;
  if (token) metadata.authorization = `Bearer ${token}`;

  if (deadlineMs !== null) {
    // grpc-web attend un TIMESTAMP ABSOLU en millisecondes, sous forme de
    // chaîne : il le retire des headers et le convertit en `grpc-timeout`.
    metadata.deadline = String(Date.now() + deadlineMs);
  }

  return metadata;
}

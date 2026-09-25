import type { Metadata } from "grpc-web";

// Les METADATA sont les "headers" de gRPC (4.5) : des paires clé/valeur
// envoyées À CÔTÉ de la requête, hors du contrat .proto. En grpc-web, c'est
// le 2e argument de chaque appel — pas un objet d'options séparé.

/** Deadline par défaut des appels bornés (règle de prod du 4.4). */
export const DEFAULT_DEADLINE_MS = 5000;

const JWT_KEY = "jwt";

export function setJwt(token: string): void {
  sessionStorage.setItem(JWT_KEY, token);
}

export function clearJwt(): void {
  sessionStorage.removeItem(JWT_KEY);
}

export function getJwt(): string {
  return sessionStorage.getItem(JWT_KEY) ?? import.meta.env.VITE_GRPC_TOKEN ?? "";
}

/**
 * Metadata communes à tous les appels.
 *
 * @param deadlineMs durée max de l'appel ; `null` pour un flux sans fin
 * @param options.skipAuth pour Login (RPC public)
 */
export function callMetadata(
  deadlineMs: number | null = DEFAULT_DEADLINE_MS,
  options: { skipAuth?: boolean } = {},
): Metadata {
  const metadata: Metadata = {
    "x-client-app": "react-web",
    "x-request-id": crypto.randomUUID(),
  };

  if (!options.skipAuth) {
    const token = getJwt();
    if (token) metadata.authorization = `Bearer ${token}`;
  }

  if (deadlineMs !== null) {
    metadata.deadline = String(Date.now() + deadlineMs);
  }

  return metadata;
}

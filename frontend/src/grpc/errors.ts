import { StatusCode } from "grpc-web";
import type { RpcError } from "grpc-web";

// Le serveur renvoie des status codes STANDARDISÉS (Module 2.5) ; le front les
// traduit en messages lisibles et dit si l'action vaut la peine d'être relancée.

export interface UiError {
  /** Message affichable tel quel à l'utilisateur. */
  message: string;
  /** true = erreur transitoire (réseau, délai) → proposer « Réessayer ». */
  retryable: boolean;
}

export function grpcErrorMessage(err: unknown): UiError {
  const rpcError = err as RpcError | undefined;
  const code = rpcError?.code;
  // Le `details` de Python (context.abort) arrive dans `message` côté grpc-web
  const details = rpcError?.message?.trim();

  switch (code) {
    case StatusCode.INVALID_ARGUMENT: // 3 — le client a mal rempli quelque chose
      return {
        message: details
          ? `Données invalides : ${details}`
          : "Données invalides : vérifiez le formulaire.",
        retryable: false,
      };
    case StatusCode.DEADLINE_EXCEEDED: // 4 — le deadline du 4.4 a sauté
      return { message: "Délai dépassé, réessayez.", retryable: true };
    case StatusCode.NOT_FOUND: // 5
      return { message: "Ressource introuvable.", retryable: false };
    case StatusCode.PERMISSION_DENIED: // 7
      return { message: "Accès refusé.", retryable: false };
    case StatusCode.UNAUTHENTICATED: // 16 — metadata `authorization` absente/invalide
      return { message: "Session expirée, reconnectez-vous.", retryable: false };
    case StatusCode.UNAVAILABLE: // 14 — serveur injoignable
    case StatusCode.UNKNOWN: // 2 — cas réel du proxy éteint : sans réponse HTTP,
      // le navigateur n'a aucun `grpc-status` et grpc-web retombe sur UNKNOWN
      return { message: "Serveur momentanément indisponible.", retryable: true };
    case StatusCode.CANCELLED: // 1 — flux coupé en cours de route
      return { message: "Connexion interrompue.", retryable: true };
    default:
      return { message: "Erreur inattendue. Réessayez.", retryable: true };
  }
}

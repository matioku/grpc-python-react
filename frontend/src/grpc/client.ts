import { StatusCode } from "grpc-web";
import { ChatServiceClient } from "generated/ChatServiceClientPb";
// ↑ le stub client GÉNÉRÉ au 3.3 (npm run proto) — équivalent du ChatServiceStub Python.
//   "generated" est le paquet local src/generated (voir vite.config.ts).

// Adresse du PROXY Envoy (8080), PAS du serveur Python (50051) !
// Le navigateur parle grpc-web ; Envoy traduit en gRPC natif pour Python.
// Si 8080 est déjà pris : publier Envoy sur un autre port (-p 18080:8080)
// et lancer le front avec VITE_GRPC_URL=http://localhost:18080 npm run dev.
export const client = new ChatServiceClient(
  import.meta.env.VITE_GRPC_URL ?? "http://localhost:8080", // Envoy (CORS autorisé dans envoy.yaml)
  null, // credentials (null = pas d'auth pour l'instant)
  null, // options avancées (null = défauts)
);
// C'est le pendant du channel Python : grpc.insecure_channel("localhost:50051").

// Code numérique → nom, comme err.code().name en Python (3 → "INVALID_ARGUMENT").
// L'objet StatusCode de grpc-web n'a pas de mapping inverse (StatusCode[3] === undefined).
export function statusName(code: number): string {
  const entry = Object.entries(StatusCode).find(([, value]) => value === code);
  return entry ? entry[0] : `CODE_${code}`;
}

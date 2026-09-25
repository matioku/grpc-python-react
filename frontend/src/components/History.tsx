import { useEffect, useState } from "react";
import type { RpcError } from "grpc-web";
import { ChatMessage, HistoryRequest } from "generated/chat_pb";
import { client, statusName } from "../grpc/client";
import { callMetadata } from "../grpc/metadata";

export function History({ user }: { user: string }) {
  const [messages, setMessages] = useState<string[]>([]);
  const [error, setError] = useState("");
  // Exercice 2 : changer cette clé relance le useEffect → nouveau stream
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    // Filtre serveur : uniquement les messages de CET utilisateur (login).
    const request = new HistoryRequest().setUser(user);

    // Le stream reste ouvert : à chaque message reçu, on ajoute à l'état React
    // 2e argument = metadata (4.5) + deadline (4.4) : un historique doit
    // arriver vite, sinon autant prévenir l'utilisateur.
    setMessages([]);
    const stream = client.history(request, callMetadata());
    stream.on("data", (msg: ChatMessage) => {
      // Exercice 1 : on affiche aussi l'auteur (getUser())
      setMessages((prev) => [
        ...prev,
        `[${msg.getTimestamp()}] ${msg.getUser()} : ${msg.getText()}`,
      ]);
    });
    stream.on("error", (err: RpcError) => {
      console.error("Erreur stream :", err);
      setError(`${statusName(err.code)} (${err.code}) : ${err.message}`);
    });
    stream.on("end", () => console.log("Stream terminé"));

    // Nettoyage : au démontage OU avant de relancer (Actualiser), on FERME le flux
    return () => stream.cancel();
  }, [refreshKey, user]); // se ré-abonne à chaque clic sur "Actualiser"

  // Exercice 2 : on vide la liste puis on change la clé → cancel() de l'ancien
  // stream (cleanup) et ouverture d'un nouveau (effet relancé)
  const refresh = () => {
    setMessages([]);
    setError("");
    setRefreshKey((k) => k + 1);
  };

  return (
    <div>
      <h2>Historique de {user} (server streaming)</h2>
      <p style={{ color: "#666", fontSize: "0.9rem" }}>
        Messages déjà envoyés par cet utilisateur (pas le chat live — utilisez le salon
        ci-dessus). Envoyez un message puis cliquez Actualiser.
      </p>
      <button onClick={refresh}>Actualiser</button>
      {error && <p style={{ color: "red" }}>{error}</p>}
      {messages.length === 0 && !error && (
        <p style={{ color: "#888" }}>Aucun message pour « {user} » pour l’instant.</p>
      )}
      <ul>
        {messages.map((m, i) => (
          <li key={i}>{m}</li>
        ))}
      </ul>
    </div>
  );
}

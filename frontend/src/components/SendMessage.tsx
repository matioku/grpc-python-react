import { useState } from "react";
import type { RpcError } from "grpc-web";
import { ChatMessage } from "generated/chat_pb"; // classe message générée
import { client, statusName } from "../grpc/client"; // le stub du 3.5

export function SendMessage() {
  const [text, setText] = useState("");
  const [ack, setAck] = useState("");
  const [error, setError] = useState("");

  // L'appel unary : l'équivalent du stub.SendMessage() de Python !
  const send = async () => {
    setError("");
    setAck("");
    // 1. On construit la requête avec la classe générée (setUser, setText…)
    //    Pas de vérification côté client : un texte vide part au serveur,
    //    qui répond INVALID_ARGUMENT (exercice 3).
    const request = new ChatMessage()
      .setUser("Mounir")
      .setText(text)
      .setTimestamp(new Date().toISOString());

    try {
      // 2. L'appel RPC — "unary" = 1 requête, 1 réponse
      const response = await client.sendMessage(request, {});
      // 3. On lit la réponse TYPÉE (getText() existe grâce au .proto)
      setAck(response.getText());
      setText("");
    } catch (err) {
      // 4. Les erreurs gRPC arrivent ici — mêmes codes que Python ! (Module 2)
      const rpcError = err as RpcError;
      setError(`${statusName(rpcError.code)} (${rpcError.code}) : ${rpcError.message}`);
    }
  };

  return (
    <div>
      <h2>Envoyer un message (unary)</h2>
      <input
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && send()}
        placeholder="Votre message"
      />
      <button onClick={send}>Envoyer</button>
      {ack && <p style={{ color: "green" }}>{ack}</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}
    </div>
  );
}

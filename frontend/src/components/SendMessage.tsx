import { useState } from "react";
import type { RpcError } from "grpc-web";
import { ChatMessage } from "generated/chat_pb"; // classe message générée
import { client, statusName } from "../grpc/client"; // le stub du 3.5
import { grpcErrorMessage } from "../grpc/errors";
import { callMetadata } from "../grpc/metadata";

export function SendMessage({ defaultUser = "Mounir" }: { defaultUser?: string }) {
  const [text, setText] = useState("");
  const [ack, setAck] = useState("");
  const [error, setError] = useState("");
  const [canRetry, setCanRetry] = useState(false); // Module 4.6

  // L'appel unary : l'équivalent du stub.SendMessage() de Python !
  const send = async () => {
    setError("");
    setAck("");
    // 1. On construit la requête avec la classe générée (setUser, setText…)
    //    Pas de vérification côté client : un texte vide part au serveur,
    //    qui répond INVALID_ARGUMENT (exercice 3).
    const request = new ChatMessage()
      .setUser(defaultUser)
      .setText(text)
      .setTimestamp(new Date().toISOString());

    try {
      // 2. L'appel RPC — "unary" = 1 requête, 1 réponse.
      //    2e argument = les METADATA (4.5), qui portent aussi le deadline (4.4).
      const response = await client.sendMessage(request, callMetadata());
      // 3. On lit la réponse TYPÉE (getText() existe grâce au .proto)
      setAck(response.getText());
      setText("");
      setCanRetry(false);
    } catch (err) {
      // 4. Module 4.6 : le code gRPC devient un message humain…
      const { message, retryable } = grpcErrorMessage(err);
      const code = (err as RpcError).code;
      // … et on garde le code technique, utile pendant le cours.
      setError(`${message} [${statusName(code)} ${code}]`);
      setCanRetry(retryable);
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
      {error && (
        <p style={{ color: "red" }}>
          {error}{" "}
          {canRetry && (
            <button type="button" onClick={send}>
              Réessayer
            </button>
          )}
        </p>
      )}
    </div>
  );
}

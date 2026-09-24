import { useEffect, useRef, useState } from "react";
import { useChat } from "../hooks/useChat";

// Ici : QUE de l'affichage. Tout le gRPC est dans useChat (hooks = gRPC,
// composants = UI).
export function ChatRoom({ myName }: { myName: string }) {
  const { messages, send, connected, error, canRetry, retry } = useChat(myName);
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  // Défilement automatique vers le bas à chaque nouveau message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault(); // empêche le rechargement de la page
    void send(input);
    setInput("");
  };

  return (
    <div>
      <h2>💬 Chat temps réel {connected ? "🟢" : "🔴"}</h2>

      {error && (
        <p style={{ color: "red" }}>
          {error}{" "}
          {canRetry && (
            <button type="button" onClick={retry}>
              Réessayer
            </button>
          )}
        </p>
      )}

      {/* La fenêtre de messages : hauteur fixe, défilement auto */}
      <div style={{ height: 300, overflowY: "auto", border: "1px solid #ccc", padding: 8 }}>
        {messages.map((m) => (
          <div key={m.id} style={{ textAlign: m.mine ? "right" : "left" }}>
            <strong>{m.user}</strong>{" "}
            <span style={{ color: "#666", fontSize: 12 }}>({m.timestamp})</span>
            <div>{m.text}</div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Formulaire d'envoi */}
      <form onSubmit={handleSubmit} style={{ display: "flex", marginTop: 8 }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Votre message..."
          style={{ flex: 1, marginRight: 8 }}
        />
        <button type="submit" disabled={!connected}>
          Envoyer
        </button>
      </form>
    </div>
  );
}

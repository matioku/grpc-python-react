import { useState } from "react";
import { ChatRoom } from "./components/ChatRoom";
import { SendMessage } from "./components/SendMessage";
import { History } from "./components/History";

export default function App() {
  // Le pseudo identifie l'abonné côté serveur : ouvrez deux onglets avec
  // deux pseudos différents pour voir le temps réel.
  const [myName, setMyName] = useState("");
  const [draft, setDraft] = useState("");

  return (
    <main style={{ fontFamily: "sans-serif", maxWidth: 600, margin: "2rem auto" }}>
      <h1>⚛️ Chat gRPC — React + Python</h1>

      {myName ? (
        <ChatRoom myName={myName} />
      ) : (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            setMyName(draft.trim());
          }}
        >
          <label>
            Votre pseudo :{" "}
            <input value={draft} onChange={(e) => setDraft(e.target.value)} placeholder="Mounir" />
          </label>{" "}
          <button type="submit" disabled={!draft.trim()}>
            Entrer dans le chat
          </button>
        </form>
      )}

      <hr />
      <SendMessage />
      <hr />
      <History />
    </main>
  );
}

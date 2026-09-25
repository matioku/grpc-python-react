import { useState } from "react";
import { ChatRoom } from "./components/ChatRoom";
import { SendMessage } from "./components/SendMessage";
import { History } from "./components/History";
import { LoginForm } from "./components/LoginForm";
import { clearJwt, getJwt } from "./grpc/metadata";

export default function App() {
  const [myName, setMyName] = useState(() => (getJwt() ? sessionStorage.getItem("chatUser") ?? "" : ""));

  const onLoggedIn = (user: string) => {
    sessionStorage.setItem("chatUser", user);
    setMyName(user);
  };

  const logout = () => {
    clearJwt();
    sessionStorage.removeItem("chatUser");
    setMyName("");
  };

  return (
    <main style={{ fontFamily: "sans-serif", maxWidth: 600, margin: "2rem auto" }}>
      <h1>⚛️ Chat gRPC — React + Python</h1>

      {myName ? (
        <>
          <p>
            Connecté en tant que <strong>{myName}</strong>{" "}
            <button type="button" onClick={logout}>
              Déconnexion
            </button>
          </p>
          <ChatRoom myName={myName} />
        </>
      ) : (
        <LoginForm onLoggedIn={onLoggedIn} />
      )}

      {myName && (
        <>
          <hr />
          <SendMessage defaultUser={myName} />
          <hr />
          <History user={myName} />
        </>
      )}
    </main>
  );
}

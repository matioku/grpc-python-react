import { useState, type FormEvent } from "react";
import type { RpcError } from "grpc-web";
import { LoginRequest } from "generated/chat_pb";
import { client, statusName } from "../grpc/client";
import { callMetadata, setJwt } from "../grpc/metadata";
import { grpcErrorMessage } from "../grpc/errors";

interface Props {
  onLoggedIn: (user: string) => void;
}

/** Écran de login (Module 5 — exercice 3) : appelle Login, stocke le JWT. */
export function LoginForm({ onLoggedIn }: Props) {
  const [username, setUsername] = useState("mounir");
  const [password, setPassword] = useState("password");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    const request = new LoginRequest().setUsername(username).setPassword(password);
    try {
      const response = await client.login(request, callMetadata(5000, { skipAuth: true }));
      setJwt(response.getToken());
      onLoggedIn(response.getUser());
    } catch (err) {
      const { message } = grpcErrorMessage(err);
      const code = (err as RpcError).code;
      setError(`${message} [${statusName(code)}]`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={submit}>
      <h2>Connexion</h2>
      <p style={{ color: "#555", fontSize: "0.9rem" }}>
        Comptes démo : <code>mounir</code> / <code>alice</code> / <code>bob</code> — mot de passe{" "}
        <code>password</code>
      </p>
      <label>
        Utilisateur :{" "}
        <input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" />
      </label>{" "}
      <label>
        Mot de passe :{" "}
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
        />
      </label>{" "}
      <button type="submit" disabled={loading || !username.trim()}>
        {loading ? "…" : "Se connecter"}
      </button>
      {error && <p style={{ color: "red" }}>{error}</p>}
    </form>
  );
}

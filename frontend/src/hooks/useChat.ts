import { useCallback, useEffect, useRef, useState } from "react";
import type { RpcError } from "grpc-web";
import { ChatMessage, SubscribeRequest } from "generated/chat_pb";
import { client } from "../grpc/client";
import { grpcErrorMessage } from "../grpc/errors";
import { callMetadata } from "../grpc/metadata";

// La forme d'un message côté UI (découplée du type protobuf)
export interface UiMessage {
  id: number;
  user: string;
  text: string;
  timestamp: string;
  mine: boolean; // true = envoyé par MOI (pour l'aligner à droite)
}

/**
 * Le chat temps réel, en DEUX flux (limite grpc-web) :
 *
 *   descendant : Subscribe — un stream serveur ouvert tant que l'onglet vit
 *   montant    : SendMessage — un appel unary par message envoyé
 *
 * Le serveur diffuse chaque message à tous les abonnés : nos propres messages
 * nous reviennent donc par le flux descendant, comme ceux des autres.
 */
export function useChat(myName: string) {
  const [messages, setMessages] = useState<UiMessage[]>([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState("");
  const [canRetry, setCanRetry] = useState(false);
  const [attempt, setAttempt] = useState(0); // changer cette clé rouvre le flux
  const counter = useRef(0); // ids de repli, survit aux re-rendus
  const lastFailed = useRef(""); // exercice 3 : le texte à réenvoyer

  // ---------- CONNEXION : le flux DESCENDANT, ouvert une seule fois ----------
  useEffect(() => {
    if (!myName) return;

    // Pas de deadline sur ce flux : il doit durer aussi longtemps que l'onglet.
    const request = new SubscribeRequest().setUser(myName);
    const stream = client.subscribe(request, callMetadata(null));

    // Un stream gRPC est un système EXTERNE : il n'existe qu'APRÈS le montage.
    // L'état "connecté" ne peut donc être posé qu'ici (grpc-web ne signale pas
    // l'arrivée des headers : son évènement "metadata" n'est émis qu'à la
    // fermeture du flux — inutilisable comme signal de connexion).
    // oxlint-disable-next-line react/set-state-in-effect
    setError("");
    // oxlint-disable-next-line react/set-state-in-effect
    setConnected(true);

    // Vrai quand c'est NOUS qui fermons : le cancel() déclenche un "error"
    // CANCELLED qu'il ne faut pas afficher comme une panne.
    let closing = false;

    // Chaque message POUSSÉ par le serveur (broadcast du Module 2, §2.3)
    stream.on("data", (msg: ChatMessage) => {
      setMessages((prev) => [
        ...prev,
        {
          id: msg.getId() || ++counter.current, // id serveur = key React stable
          user: msg.getUser(),
          text: msg.getText(),
          timestamp: msg.getTimestamp(),
          mine: msg.getUser() === myName,
        },
      ]);
    });

    stream.on("error", (err: RpcError) => {
      if (closing) return;
      setConnected(false);
      const { message, retryable } = grpcErrorMessage(err);
      setError(`Connexion perdue : ${message}`);
      setCanRetry(retryable);
    });

    stream.on("end", () => setConnected(false));

    // Nettoyage au démontage : on FERME le flux (règle d'or du Module 3),
    // sinon le serveur garde une queue qui se remplit dans le vide.
    return () => {
      closing = true;
      stream.cancel();
      setConnected(false);
    };
  }, [myName, attempt]); // si myName change, on se reconnecte

  // ---------- ENVOI : un appel unary borné par un deadline (4.4) ----------
  const send = useCallback(
    async (text: string) => {
      if (!text.trim()) return;
      const request = new ChatMessage()
        .setUser(myName)
        .setText(text)
        .setTimestamp(new Date().toISOString());

      try {
        await client.sendMessage(request, callMetadata());
        setError("");
        setCanRetry(false);
        lastFailed.current = "";
      } catch (err) {
        const { message, retryable } = grpcErrorMessage(err);
        setError(message);
        setCanRetry(retryable);
        lastFailed.current = retryable ? text : "";
      }
    },
    [myName],
  );

  // ---------- Exercice 3 : relancer ce qui a échoué ----------
  const retry = useCallback(() => {
    setCanRetry(false);
    if (lastFailed.current) {
      void send(lastFailed.current); // un envoi qui n'est pas passé
    } else {
      setAttempt((n) => n + 1); // sinon c'est le flux qui est tombé
    }
  }, [send]);

  return { messages, send, connected, error, canRetry, retry };
}

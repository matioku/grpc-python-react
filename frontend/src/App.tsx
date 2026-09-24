import { SendMessage } from "./components/SendMessage";
import { History } from "./components/History";

export default function App() {
  return (
    <main style={{ fontFamily: "sans-serif", maxWidth: 600, margin: "2rem auto" }}>
      <h1>⚛️ Chat gRPC — React + Python</h1>
      <SendMessage />
      <hr />
      <History />
    </main>
  );
}

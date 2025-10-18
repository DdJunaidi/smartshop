import { useState, useEffect, useRef } from "react";
import { chatReply } from "../api";

/**
 * Tiny floating chatbot. Sends single-turn messages to the backend.
 * You can replace with streaming & history later.
 */
export default function ChatbotWidget() {
  const [open, setOpen] = useState(true);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [messages, setMessages] = useState([
    { role: "assistant", text: "Hi! I’m your Shopping Assistant. Ask me about products, specs, or deals." }
  ]);
  const boxRef = useRef(null);

  useEffect(() => {
    if (boxRef.current) boxRef.current.scrollTop = boxRef.current.scrollHeight;
  }, [messages, open]);

  async function send() {
    const text = input.trim();
    if (!text || sending) return;
    const next = [...messages, { role: "user", text }];
    setMessages(next);
    setInput("");
    setSending(true);
    try {
      const r = await chatReply(next);
      let rep = r?.data?.reply;
      if (typeof rep === "string") rep = { role: "assistant", text: rep };
      if (!rep?.text) rep = { role: "assistant", text: "Hmm, I couldn't reply just now." };
      setMessages([...next, rep]);
    } catch {
      setMessages([...next, { role: "assistant", text: "Sorry, I hit an error. Try again." }]);
    } finally {
      setSending(false);
    }
  }

  function onKey(e) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
  }

  return (
    <div style={{ position: "fixed", right: 24, bottom: 24, width: 360, zIndex: 50 }}>
      <div style={{ background: "#0f1115", color: "#fff", border: "1px solid #2a2a2e",
                    borderRadius: 12, overflow: "hidden", boxShadow: "0 4px 20px rgba(0,0,0,.4)" }}>
        <div style={{ display: "flex", alignItems: "center", padding: "10px 12px", background: "#12151b" }}>
          <strong style={{ flex: 1 }}>Shopping Assistant</strong>
          <button onClick={() => setOpen(!open)} style={{ background: "#2b59ff" }}>
            {open ? "×" : "Open"}
          </button>
        </div>

        {open && (
          <>
            <div ref={boxRef}
                 style={{ maxHeight: 280, overflowY: "auto", padding: 12, display: "flex",
                          flexDirection: "column", gap: 8 }}>
              {messages.map((m, i) => (
                <div key={i}
                     style={{ alignSelf: m.role === "user" ? "flex-end" : "flex-start",
                              background: m.role === "user" ? "#2b59ff" : "#1b1f2a",
                              color: "#fff", padding: "8px 10px", borderRadius: 10, maxWidth: "85%" }}>
                  {m.text}
                </div>
              ))}
            </div>

            <div style={{ padding: 12, borderTop: "1px solid #2a2a2e" }}>
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={onKey}
                rows={2}
                placeholder="Ask about products, specs, availability…"
                style={{ width: "100%", resize: "none", borderRadius: 8, padding: 8 }}
              />
              <button onClick={send} disabled={sending} style={{ marginTop: 8 }}>
                {sending ? "Thinking…" : "Send"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

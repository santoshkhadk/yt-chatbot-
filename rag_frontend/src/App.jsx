import { useState } from "react";
import axios from "axios";

function App() {
  const [url, setUrl] = useState("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");

  const askQuestion = async () => {
    if (!url || !question) return;

    try {
      const res = await axios.post("http://127.0.0.1:8000/api/ask/", {
        url,
        question
      });
      setAnswer(res.data.answer);
    } catch (err) {
      console.error(err);
      setAnswer("Error fetching answer.");
    }
  };

  return (
    <div style={{ padding: "40px" }}>
      <h1>YouTube AI Chatbot</h1>

      <input
        type="text"
        placeholder="Paste YouTube URL..."
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        style={{ width: "400px", marginBottom: "10px" }}
      />
      <br />

      <input
        type="text"
        placeholder="Ask a question..."
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        style={{ width: "400px" }}
      />
      <br />
      <button onClick={askQuestion} style={{ marginTop: "10px" }}>
        Ask
      </button>

      <h3>Answer:</h3>
      <p>{answer}</p>
    </div>
  );
}

export default App;
import { useState } from "react";
import axios from "axios";

function App() {
  const [urls, setUrls] = useState([""]); // start with one input
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");

  const handleUrlChange = (index, value) => {
    const newUrls = [...urls];
    newUrls[index] = value;
    setUrls(newUrls);
  };

  const addUrlInput = () => {
    setUrls([...urls, ""]);
  };

  const removeUrlInput = (index) => {
    setUrls(urls.filter((_, i) => i !== index));
  };

  const askQuestion = async () => {
    const urlArray = urls.map((u) => u.trim()).filter((u) => u);
    if (urlArray.length === 0 || !question) return;

    try {
      const res = await axios.post("http://127.0.0.1:8000/api/ask/", {
        urls: urlArray,
        question,
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

      {urls.map((url, index) => (
        <div key={index} style={{ marginBottom: "8px" }}>
          <input
            type="text"
            placeholder={`YouTube URL #${index + 1}`}
            value={url}
            onChange={(e) => handleUrlChange(index, e.target.value)}
            style={{ width: "300px" }}
          />
          {urls.length > 1 && (
            <button onClick={() => removeUrlInput(index)} style={{ marginLeft: "5px" }}>
              Remove
            </button>
          )}
        </div>
      ))}

      <button onClick={addUrlInput} style={{ marginBottom: "10px" }}>
        Add another URL
      </button>
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
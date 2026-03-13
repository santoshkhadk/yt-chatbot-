import { useState } from "react";
import axios from "axios";

function App() {
  const [urls, setUrls] = useState([""]);
  const [file, setFile] = useState(null);
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

  const askQuestion = async () => {
    const urlArray = urls.filter((u) => u.trim() !== "");

    const formData = new FormData();
    formData.append("question", question);

    urlArray.forEach((url) => {
      formData.append("urls", url);
    });

    if (file) {
      formData.append("transcript_file", file);
    }

    try {
      const res = await axios.post(
        "http://127.0.0.1:8000/api/ask/",
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );

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
        <div key={index}>
          <input
            type="text"
            placeholder={`YouTube URL ${index + 1}`}
            value={url}
            onChange={(e) => handleUrlChange(index, e.target.value)}
            style={{ width: "350px", marginBottom: "5px" }}
          />
        </div>
      ))}

      <button onClick={addUrlInput}>Add URL</button>

      <br /><br />

      <input
        type="file"
        accept=".txt,.pdf"
        onChange={(e) => setFile(e.target.files[0])}
      />

      <br /><br />

      <input
        type="text"
        placeholder="Ask a question..."
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        style={{ width: "400px" }}
      />

      <br /><br />

      <button onClick={askQuestion}>Ask</button>

      <h3>Answer:</h3>
      <p>{answer}</p>
    </div>
  );
}

export default App;
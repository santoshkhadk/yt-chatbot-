import { useState } from "react";
import axios from "axios";

function App() {

  const [urls, setUrls] = useState([""]);
  const [file, setFile] = useState(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);

  const handleUrlChange = (index, value) => {
    const newUrls = [...urls];
    newUrls[index] = value;
    setUrls(newUrls);
  };

  const addUrlInput = () => {
    setUrls([...urls, ""]);
  };

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, "0")}`;
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
      setSources(res.data.sources || []);

    } catch (err) {

      console.error(err);
      setAnswer("Error fetching answer.");
      setSources([]);

    }

  };

  return (

    <div style={{ padding: "40px", fontFamily: "Arial" }}>

      <h1>YouTube RAG Chatbot</h1>

      <h3>YouTube URLs</h3>

      {urls.map((url, index) => (
        <div key={index}>

          <input
            type="text"
            placeholder={`YouTube URL ${index + 1}`}
            value={url}
            onChange={(e) => handleUrlChange(index, e.target.value)}
            style={{ width: "400px", marginBottom: "5px" }}
          />

        </div>
      ))}

      <button onClick={addUrlInput}>Add URL</button>

      <br /><br />

      <h3>Upload Transcript (optional)</h3>

      <input
        type="file"
        accept=".txt,.pdf"
        onChange={(e) => setFile(e.target.files[0])}
      />

      <br /><br />

      <h3>Ask Question</h3>

      <input
        type="text"
        placeholder="Ask something about the video..."
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        style={{ width: "500px" }}
      />

      <br /><br />

      <button onClick={askQuestion}>Ask</button>

      <hr />

      <h2>Answer</h2>

      <p>{answer}</p>

      {sources.length > 0 && (
        <>
          <h2>Sources</h2>

          {sources.map((src, index) => (

            <div
              key={index}
              style={{
                border: "1px solid #ddd",
                padding: "10px",
                marginBottom: "10px",
                borderRadius: "6px"
              }}
            >

              <a
                href={src.link}
                target="_blank"
                rel="noopener noreferrer"
              >
                ▶ Watch at {formatTime(src.timestamp)}
              </a>

              <p>{src.text}</p>

            </div>

          ))}

        </>
      )}

    </div>

  );

}

export default App;
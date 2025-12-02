import React, { useState } from 'react';
import './App.css';
import { executeAgent, listAgents } from './api/client';

function App() {
  const [response, setResponse] = useState<string>('');
  const [loading, setLoading] = useState(false);

  const handleExecute = async () => {
    setLoading(true);
    try {
      const result = await executeAgent('simple_agent', { query: 'test query' });
      setResponse(JSON.stringify(result, null, 2));
    } catch (error) {
      setResponse(`Error: ${error}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>AI Devtools Hack</h1>
        <button onClick={handleExecute} disabled={loading}>
          {loading ? 'Loading...' : 'Execute Agent'}
        </button>
        <pre>{response}</pre>
      </header>
    </div>
  );
}

export default App;

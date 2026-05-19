import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import config from '../api/config';
import './PatientAnalysis.css';

function PatientAnalysis() {
  const [conditions, setConditions] = useState('');
  const [allergies, setAllergies] = useState('');
  const [medications, setMedications] = useState('');
  const [analysis, setAnalysis] = useState('');
  const [loading, setLoading] = useState(false);

  const handleAnalyze = async (e) => {
    e.preventDefault();
    setLoading(true);
    setAnalysis('');

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${config.API_URL}/api/drugs/analyze-patient`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          chronic_conditions: conditions
            .split(',')
            .map((s) => s.trim())
            .filter(Boolean),
          allergies: allergies
            .split(',')
            .map((s) => s.trim())
            .filter(Boolean),
          current_medications: medications
            .split(',')
            .map((s) => s.trim())
            .filter(Boolean),
        }),
      });

      // Audit F11: check `response.ok` before assuming the body is valid JSON.
      // The backend can legitimately return 4xx/5xx with a non-JSON body
      // (e.g. nginx 502 HTML), and the previous code blew up parsing it.
      if (!response.ok) {
        let detail = `Request failed with status ${response.status}`;
        try {
          const errBody = await response.json();
          if (errBody?.detail) detail = `${detail}: ${errBody.detail}`;
        } catch {
          // Body wasn't JSON; keep the status-based message.
        }
        setAnalysis(`Error: ${detail}`);
        return;
      }

      const data = await response.json();
      if (data.success) {
        setAnalysis(data.analysis);
      } else {
        setAnalysis('Error: ' + (data.error || 'Unknown error'));
      }
    } catch {
      // Audit F8: don't echo internal error details to the console in
      // production. A friendly message is enough for the user.
      setAnalysis('Error: Could not connect to server');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="patient-analysis">
      <h1>🏥 Patient Medical Profile Analysis</h1>

      <form onSubmit={handleAnalyze} className="analysis-form">
        <div className="form-group">
          <label>Chronic Conditions (comma-separated)</label>
          <input
            type="text"
            value={conditions}
            onChange={(e) => setConditions(e.target.value)}
            placeholder="e.g., Type 2 Diabetes, Hypertension"
          />
        </div>

        <div className="form-group">
          <label>Allergies (comma-separated)</label>
          <input
            type="text"
            value={allergies}
            onChange={(e) => setAllergies(e.target.value)}
            placeholder="e.g., Penicillin, Sulfa drugs"
          />
        </div>

        <div className="form-group">
          <label>Current Medications (comma-separated)</label>
          <input
            type="text"
            value={medications}
            onChange={(e) => setMedications(e.target.value)}
            placeholder="e.g., Metformin, Lisinopril, Aspirin"
          />
        </div>

        <button type="submit" disabled={loading}>
          {loading ? 'Analyzing...' : 'Analyze Profile'}
        </button>
      </form>

      {analysis && (
        <div className="analysis-result">
          <h2>Analysis Results</h2>
          {/*
            Audit F7: backend can return Markdown (headings, bullet lists,
            tables). Render it through ReactMarkdown rather than dumping it
            as raw text. We deliberately avoid `rehype-raw` here for the
            same XSS reasons as MarkdownWithReferences.
          */}
          <div className="result-content">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{analysis}</ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}

export default PatientAnalysis;

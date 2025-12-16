import { useState } from 'react';
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
      const response = await fetch('http://localhost:3001/api/drugs/analyze-patient', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          chronic_conditions: conditions.split(',').map(s => s.trim()).filter(Boolean),
          allergies: allergies.split(',').map(s => s.trim()).filter(Boolean),
          current_medications: medications.split(',').map(s => s.trim()).filter(Boolean)
        })
      });

      const data = await response.json();
      if (data.success) {
        setAnalysis(data.analysis);
      } else {
        setAnalysis('Error: ' + (data.error || 'Unknown error'));
      }
    } catch (error) {
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
          <div className="result-content">{analysis}</div>
        </div>
      )}
    </div>
  );
}

export default PatientAnalysis;

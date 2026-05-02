import React from 'react';
import './ConfidenceBreakdown.css';

/**
 * Display confidence score breakdown for PubMed articles.
 * 
 * Shows the individual components that make up the overall confidence score:
 * - Citations: Based on citation count
 * - Recency: How recent the article is
 * - Evidence Level: Publication type quality (RCT > case study, etc.)
 * - Relevance: How well it matches the search query
 */
function ConfidenceBreakdown({ breakdown, overallScore }) {
  if (!breakdown) return null;

  const components = [
    {
      name: 'Citations',
      score: breakdown.citations || 0,
      icon: '📊',
      description: 'Based on citation count',
    },
    {
      name: 'Recency',
      score: breakdown.recency || 0,
      icon: '📅',
      description: 'How recent the publication is',
    },
    {
      name: 'Evidence Level',
      score: breakdown.evidence_level || 0,
      icon: '🔬',
      description: 'Publication type quality',
    },
    {
      name: 'Relevance',
      score: breakdown.relevance || 0,
      icon: '🎯',
      description: 'Match to search query',
    },
  ];

  const getScoreColor = (score) => {
    if (score >= 70) return '#10b981'; // green
    if (score >= 40) return '#f59e0b'; // orange
    return '#ef4444'; // red
  };

  return (
    <div className="confidence-breakdown">
      <div className="confidence-breakdown-header">
        <span className="confidence-breakdown-title">Confidence Score Breakdown</span>
        <span 
          className="confidence-breakdown-overall"
          style={{ color: getScoreColor(overallScore) }}
        >
          Overall: {overallScore}/100
        </span>
      </div>

      <div className="confidence-breakdown-grid">
        {components.map((component) => (
          <div key={component.name} className="confidence-component">
            <div className="confidence-component-header">
              <span className="confidence-component-icon">{component.icon}</span>
              <span className="confidence-component-name">{component.name}</span>
            </div>
            
            <div className="confidence-component-bar-container">
              <div 
                className="confidence-component-bar"
                style={{ 
                  width: `${component.score}%`,
                  backgroundColor: getScoreColor(component.score)
                }}
              />
            </div>
            
            <div className="confidence-component-footer">
              <span 
                className="confidence-component-score"
                style={{ color: getScoreColor(component.score) }}
              >
                {component.score}/100
              </span>
              <span className="confidence-component-description">
                {component.description}
              </span>
            </div>
          </div>
        ))}
      </div>

      {breakdown.publication_types && breakdown.publication_types.length > 0 && (
        <div className="confidence-breakdown-footer">
          <span className="confidence-breakdown-label">Study Type:</span>
          <span className="confidence-breakdown-value">
            {breakdown.publication_types.join(', ')}
          </span>
        </div>
      )}
    </div>
  );
}

export default ConfidenceBreakdown;

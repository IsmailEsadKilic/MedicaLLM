import React from 'react';
import './ConfidenceBreakdown.css';

/**
 * Display confidence score breakdown for PubMed articles.
 * 
 * Shows the individual components that make up the overall confidence score:
 * - Citations: Based on citation count
 * - FWCI: Field-Weighted Citation Impact (field-normalized citations)
 * - Journal Quality: Based on CiteScore, SJR, SNIP, percentile
 * - Recency: How recent the article is
 * - Evidence Level: Publication type quality (RCT > case study, etc.)
 * - Relevance: How well it matches the search query
 */
function ConfidenceBreakdown({ breakdown, overallScore, article }) {
  if (!breakdown) return null;

  const components = [
    {
      name: 'Citations',
      score: breakdown.citations || 0,
      icon: '📊',
      description: 'Citation count',
    },
    {
      name: 'FWCI',
      score: breakdown.fwci || 0,
      icon: '📈',
      description: 'Field-normalized impact',
    },
    {
      name: 'Journal Quality',
      score: breakdown.journal_quality || 0,
      icon: '🏆',
      description: 'Journal metrics',
    },
    {
      name: 'Recency',
      score: breakdown.recency || 0,
      icon: '📅',
      description: 'Publication recency',
    },
    {
      name: 'Evidence Level',
      score: breakdown.evidence_level || 0,
      icon: '🔬',
      description: 'Study type quality',
    },
    {
      name: 'Relevance',
      score: breakdown.relevance || 0,
      icon: '🎯',
      description: 'Query match',
    },
  ];

  const getScoreColor = (score) => {
    if (score >= 70) return '#10b981'; // green
    if (score >= 40) return '#f59e0b'; // orange
    return '#ef4444'; // red
  };

  // Extract Scopus metrics if available
  const scopusMetrics = breakdown.scopus_metrics || {};
  const hasScopusMetrics = scopusMetrics.cite_score || scopusMetrics.sjr || 
                          scopusMetrics.snip || scopusMetrics.fwci;

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

      {/* Scopus Metrics Details */}
      {hasScopusMetrics && (
        <div className="scopus-metrics-section">
          <div className="scopus-metrics-header">
            <span className="scopus-metrics-title">📊 Scopus Metrics</span>
            {article?.open_access && (
              <span className="open-access-badge">🔓 Open Access</span>
            )}
          </div>
          <div className="scopus-metrics-grid">
            {scopusMetrics.cite_score && (
              <div className="scopus-metric">
                <span className="scopus-metric-label">CiteScore:</span>
                <span className="scopus-metric-value">{scopusMetrics.cite_score.toFixed(2)}</span>
              </div>
            )}
            {scopusMetrics.sjr && (
              <div className="scopus-metric">
                <span className="scopus-metric-label">SJR:</span>
                <span className="scopus-metric-value">{scopusMetrics.sjr.toFixed(2)}</span>
              </div>
            )}
            {scopusMetrics.snip && (
              <div className="scopus-metric">
                <span className="scopus-metric-label">SNIP:</span>
                <span className="scopus-metric-value">{scopusMetrics.snip.toFixed(2)}</span>
              </div>
            )}
            {scopusMetrics.journal_percentile && (
              <div className="scopus-metric">
                <span className="scopus-metric-label">Percentile:</span>
                <span className="scopus-metric-value">{scopusMetrics.journal_percentile.toFixed(0)}th</span>
              </div>
            )}
            {scopusMetrics.fwci && (
              <div className="scopus-metric">
                <span className="scopus-metric-label">FWCI:</span>
                <span className="scopus-metric-value" style={{ 
                  color: scopusMetrics.fwci >= 1.0 ? '#10b981' : '#f59e0b' 
                }}>
                  {scopusMetrics.fwci.toFixed(2)}
                  {scopusMetrics.fwci >= 1.0 ? ' ↑' : ' ↓'}
                </span>
              </div>
            )}
          </div>
          {scopusMetrics.fwci && (
            <div className="fwci-explanation">
              FWCI {scopusMetrics.fwci >= 1.0 ? 'above' : 'below'} field average 
              ({scopusMetrics.fwci >= 1.0 ? 'strong' : 'weak'} impact)
            </div>
          )}
        </div>
      )}

      {/* Query Type and Adaptive Scoring */}
      {article?.query_type && (
        <div className="query-type-section">
          <div className="query-type-header">
            <span className="query-type-icon">🎯</span>
            <span className="query-type-label">Query Type:</span>
            <span className="query-type-value">{formatQueryType(article.query_type)}</span>
          </div>
          {breakdown.weights_used && (
            <div className="weights-info">
              <span className="weights-label">Adaptive weights applied</span>
              <div className="weights-grid">
                {Object.entries(breakdown.weights_used).map(([key, value]) => (
                  <div key={key} className="weight-item">
                    <span className="weight-name">{formatWeightName(key)}:</span>
                    <span className="weight-value">{(value * 100).toFixed(0)}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Subject Areas */}
      {article?.subject_areas && article.subject_areas.length > 0 && (
        <div className="confidence-breakdown-footer">
          <span className="confidence-breakdown-label">Subject Areas:</span>
          <span className="confidence-breakdown-value">
            {article.subject_areas.join(', ')}
          </span>
        </div>
      )}

      {/* Study Type */}
      {breakdown.publication_types && breakdown.publication_types.length > 0 && (
        <div className="confidence-breakdown-footer">
          <span className="confidence-breakdown-label">Study Type:</span>
          <span className="confidence-breakdown-value">
            {breakdown.publication_types.join(', ')}
          </span>
        </div>
      )}

      {/* Citation Source */}
      {article?.citation_source && (
        <div className="confidence-breakdown-footer">
          <span className="confidence-breakdown-label">Citation Data:</span>
          <span className="confidence-breakdown-value">
            {article.citation_source === 'scopus' ? '🔵 Scopus' : 
             article.citation_source === 'semantic_scholar' ? '🟣 Semantic Scholar' : 
             '⚪ Not Available'}
          </span>
        </div>
      )}

      {/* Open Access Bonus */}
      {breakdown.open_access_bonus > 0 && (
        <div className="confidence-breakdown-footer">
          <span className="confidence-breakdown-label">Open Access Bonus:</span>
          <span className="confidence-breakdown-value" style={{ color: '#10b981' }}>
            +{breakdown.open_access_bonus} points
          </span>
        </div>
      )}
    </div>
  );
}

// Helper function to format query type for display
function formatQueryType(queryType) {
  const typeMap = {
    'author_specific': 'Author-Specific Search',
    'drug_research': 'Drug Research',
    'disease_research': 'Disease Research',
    'clinical_guideline': 'Clinical Guideline',
    'review_meta': 'Review/Meta-Analysis',
    'recent_advances': 'Recent Advances',
    'general_research': 'General Research',
  };
  return typeMap[queryType] || queryType;
}

// Helper function to format weight names for display
function formatWeightName(weightKey) {
  const nameMap = {
    'citations': 'Citations',
    'fwci': 'FWCI',
    'journal': 'Journal',
    'recency': 'Recency',
    'evidence': 'Evidence',
    'relevance': 'Relevance',
  };
  return nameMap[weightKey] || weightKey;
}

export default ConfidenceBreakdown;

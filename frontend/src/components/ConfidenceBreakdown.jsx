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
  const [openTooltip, setOpenTooltip] = React.useState(null);

  // Close tooltip when clicking anywhere outside
  React.useEffect(() => {
    if (!openTooltip) return;
    const onDocClick = () => setOpenTooltip(null);
    document.addEventListener('click', onDocClick);
    return () => document.removeEventListener('click', onDocClick);
  }, [openTooltip]);

  if (!breakdown) return null;

  // Build FWCI tooltip content
  const fwciRaw = article?.fwci;
  const fwciSource = article?.fwci_source;
  const fwciTooltip = fwciRaw != null ? (
    <>
      <div className="tooltip-row"><strong>Raw FWCI:</strong> {fwciRaw.toFixed(4)}</div>
      <div className="tooltip-row"><strong>Source:</strong> {fwciSource || '—'}</div>
      <div className="tooltip-divider" />
      <div className="tooltip-section-title">How it's scored (0–100):</div>
      <div className="tooltip-row">• FWCI ≥ 3.0 → 100</div>
      <div className="tooltip-row">• FWCI = 1.0 (field avg) → 50</div>
      <div className="tooltip-row">• FWCI = 0.0 → 0</div>
      <div className="tooltip-row">• Linear in between</div>
      <div className="tooltip-divider" />
      <div className="tooltip-row">
        <strong>Formula:</strong>{' '}
        {fwciRaw >= 3.0
          ? '100 (capped)'
          : fwciRaw >= 1.0
            ? `50 + ((${fwciRaw.toFixed(2)} − 1) / 2) × 50 = ${(50 + ((fwciRaw - 1) / 2) * 50).toFixed(1)}`
            : `${fwciRaw.toFixed(2)} × 50 = ${(fwciRaw * 50).toFixed(1)}`}
      </div>
    </>
  ) : (
    <div className="tooltip-row">FWCI not available for this article.</div>
  );

  // Build Evidence Level tooltip content
  const pubTypes = breakdown.publication_types || [];
  const evidenceLevels = {
    'meta-analysis': 100,
    'systematic review': 90,
    'randomized controlled trial': 85,
    'clinical trial': 75,
    'controlled clinical trial': 75,
    'practice guideline': 70,
    'guideline': 70,
    'comparative study': 60,
    'multicenter study': 60,
    'cohort study': 55,
    'observational study': 50,
    'journal article': 50,
    'case-control study': 45,
    'review': 40,
    'case reports': 30,
    'editorial': 15,
    'comment': 10,
    'letter': 10,
    'preprint': 10,
  };
  // Determine which type matched (highest scoring)
  let matchedType = null;
  let matchedScore = 0;
  for (const pt of pubTypes) {
    const lower = pt.toLowerCase();
    for (const [key, score] of Object.entries(evidenceLevels)) {
      if (lower.includes(key) && score > matchedScore) {
        matchedScore = score;
        matchedType = pt;
      }
    }
  }
  const evidenceTooltip = (
    <>
      <div className="tooltip-row">
        <strong>Publication types:</strong>{' '}
        {pubTypes.length > 0 ? pubTypes.join(', ') : '—'}
      </div>
      {matchedType && (
        <div className="tooltip-row">
          <strong>Matched:</strong> "{matchedType}" → {matchedScore}/100
        </div>
      )}
      <div className="tooltip-divider" />
      <div className="tooltip-section-title">Evidence hierarchy (score out of 100):</div>
      <div className="tooltip-row">• Meta-analysis → 100</div>
      <div className="tooltip-row">• Systematic review → 90</div>
      <div className="tooltip-row">• RCT → 85</div>
      <div className="tooltip-row">• Clinical trial / guideline → 70–75</div>
      <div className="tooltip-row">• Cohort / observational → 50–55</div>
      <div className="tooltip-row">• Review → 40</div>
      <div className="tooltip-row">• Case report → 30</div>
      <div className="tooltip-row">• Editorial / letter → 10–15</div>
      <div className="tooltip-divider" />
      <div className="tooltip-row">
        Score = highest match across all publication types (default 30 if none match).
      </div>
    </>
  );

  const components = [
    {
      key: 'citations',
      name: 'Citations',
      score: breakdown.citations || 0,
      icon: '📊',
      description: 'Citation count',
    },
    {
      key: 'fwci',
      name: 'FWCI',
      score: breakdown.fwci || 0,
      icon: '📈',
      description: 'Field-normalized impact',
      rawLabel: fwciRaw != null ? `Raw: ${fwciRaw.toFixed(2)}` : null,
      tooltip: fwciTooltip,
    },
    {
      key: 'journal',
      name: 'Journal Quality',
      score: breakdown.journal_quality || 0,
      icon: '🏆',
      description: 'Journal metrics',
    },
    {
      key: 'recency',
      name: 'Recency',
      score: breakdown.recency || 0,
      icon: '📅',
      description: 'Publication recency',
    },
    {
      key: 'evidence',
      name: 'Evidence Level',
      score: breakdown.evidence_level || 0,
      icon: '🔬',
      description: 'Study type quality',
      detail: pubTypes.length > 0 ? pubTypes.join(', ') : null,
      tooltip: evidenceTooltip,
    },
    {
      key: 'relevance',
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
          <div key={component.key} className="confidence-component">
            <div className="confidence-component-header">
              <span className="confidence-component-icon">{component.icon}</span>
              <span className="confidence-component-name">{component.name}</span>
              {component.tooltip && (
                <span
                  className="confidence-component-info"
                  onClick={(e) => {
                    e.stopPropagation();
                    setOpenTooltip(openTooltip === component.key ? null : component.key);
                  }}
                  role="button"
                  tabIndex={0}
                  aria-label={`Show how ${component.name} is calculated`}
                >
                  ⓘ
                  {openTooltip === component.key && (
                    <div
                      className="confidence-tooltip"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <div className="confidence-tooltip-header">
                        <span>{component.name} — how it's calculated</span>
                        <button
                          className="confidence-tooltip-close"
                          onClick={() => setOpenTooltip(null)}
                          aria-label="Close"
                        >
                          ×
                        </button>
                      </div>
                      <div className="confidence-tooltip-body">
                        {component.tooltip}
                      </div>
                    </div>
                  )}
                </span>
              )}
              {component.rawLabel && (
                <span className="confidence-component-raw">{component.rawLabel}</span>
              )}
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
            {component.detail && (
              <div className="confidence-component-detail" title={component.detail}>
                {component.detail}
              </div>
            )}
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

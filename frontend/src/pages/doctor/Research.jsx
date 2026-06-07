import { useState } from 'react';
import config from '../../api/config';
import { useT } from '../../i18n/lang';
import { DOCTOR_STRINGS } from '../../i18n/strings/doctor';
import './Research.css';

function Research() {
  const t = useT(DOCTOR_STRINGS);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [maxResults, setMaxResults] = useState(10);
  const [sortBy, setSortBy] = useState('confidence');

  const handleSearch = async (e) => {
    e?.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError('');
    setResults(null);

    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${config.API_URL}/api/pubmed/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          query: query.trim(),
          max_results: maxResults,
        }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => null);
        throw new Error(data?.detail || t.research.searchFailed(res.status));
      }

      const data = await res.json();
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const sortedArticles = results?.articles
    ? [...results.articles].sort((a, b) => {
        if (sortBy === 'confidence') return b.confidence_score - a.confidence_score;
        if (sortBy === 'citations') return b.citation_count - a.citation_count;
        if (sortBy === 'date') return (b.publication_date || '').localeCompare(a.publication_date || '');
        return 0;
      })
    : [];

  return (
    <div className="research-page">
      <div className="dashboard-header">
        <h1>{t.research.title}</h1>
        <p>{t.research.subtitle}</p>
      </div>

      {/* Search Form */}
      <form onSubmit={handleSearch} className="research-search-form">
        <div className="research-search-row">
          <input
            type="text"
            className="doctor-search-input research-input"
            placeholder={t.research.searchPlaceholder}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button type="submit" className="btn-primary research-btn" disabled={loading || !query.trim()}>
            {loading ? t.research.submitting : t.research.submit}
          </button>
        </div>
        <div className="research-options">
          <div className="research-option">
            <label>{t.research.maxResults}</label>
            <select value={maxResults} onChange={(e) => setMaxResults(Number(e.target.value))}>
              <option value={5}>5</option>
              <option value={10}>10</option>
              <option value={15}>15</option>
              <option value={20}>20</option>
            </select>
          </div>
          <div className="research-option">
            <label>{t.research.sortBy}</label>
            <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
              <option value="confidence">{t.research.sortConfidence}</option>
              <option value="citations">{t.research.sortCitations}</option>
              <option value="date">{t.research.sortDate}</option>
            </select>
          </div>
        </div>
      </form>

      {/* Error */}
      {error && (
        <div className="alert-card">
          <div className="alert-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#f87171" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
            </svg>
          </div>
          <div className="alert-content">
            <h4>{t.research.searchError}</h4>
            <p>{error}</p>
          </div>
        </div>
      )}

      {/* Results Meta */}
      {results && (
        <div className="research-meta">
          <span>{t.research.resultsCount(results.articles?.length || 0)}</span>
          <span>•</span>
          <span>{results.search_time_ms?.toFixed(0)}ms</span>
          {results.avg_confidence > 0 && (
            <>
              <span>•</span>
              <span>{t.research.avgConfidence(results.avg_confidence.toFixed(1))}</span>
            </>
          )}
          {results.filtered_count > 0 && (
            <>
              <span>•</span>
              <span>{t.research.filteredOut(results.filtered_count)}</span>
            </>
          )}
        </div>
      )}

      {/* Articles */}
      {sortedArticles.length > 0 && (
        <div className="research-results">
          {sortedArticles.map((article) => (
            <ArticleCard key={article.pmid} article={article} t={t} />
          ))}
        </div>
      )}

      {/* Empty state */}
      {results && sortedArticles.length === 0 && (
        <div className="empty-state">
          <h3>{t.research.noResults}</h3>
          <p>{t.research.tryDifferent}</p>
        </div>
      )}
    </div>
  );
}

function ArticleCard({ article, t }) {
  const [expanded, setExpanded] = useState(false);
  const [bookmarked, setBookmarked] = useState(false);

  const confidenceColor = article.confidence_score >= 70 ? '#22c55e'
    : article.confidence_score >= 50 ? '#fbbf24'
    : '#f87171';

  const toggleBookmark = async () => {
    const token = localStorage.getItem('token');
    if (bookmarked) {
      await fetch(`${config.API_URL}/api/bookmarks/${article.pmid}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      setBookmarked(false);
    } else {
      const res = await fetch(`${config.API_URL}/api/bookmarks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({
          pmid: article.pmid,
          title: article.title || '',
          authors: (article.authors || []).join(', '),
          journal: article.journal || '',
          publication_date: article.publication_date || '',
          doi: article.doi || '',
          abstract: article.abstract || '',
        }),
      });
      if (res.ok || res.status === 409) setBookmarked(true);
    }
  };

  return (
    <div className="article-card">
      <div className="article-header">
        <div className="article-score" style={{ borderColor: confidenceColor, color: confidenceColor }}>
          {article.confidence_score.toFixed(0)}
        </div>
        <div className="article-info">
          <h3 className="article-title">
            <a href={`https://pubmed.ncbi.nlm.nih.gov/${article.pmid}/`} target="_blank" rel="noopener noreferrer">
              {article.title}
            </a>
          </h3>
          <div className="article-meta">
            <span className="article-journal">{article.journal}</span>
            {article.publication_date && <span>• {article.publication_date.slice(0, 4)}</span>}
            {article.citation_count > 0 && <span>• {t.research.citationsLabel(article.citation_count)}</span>}
            {article.open_access && <span className="badge badge-med">{t.research.openAccess}</span>}
          </div>
          <div className="article-authors">
            {article.authors?.slice(0, 4).join(', ')}
            {article.authors?.length > 4 && ` ${t.research.etAl}`}
          </div>
        </div>
        <button
          className={`bookmark-btn ${bookmarked ? 'active' : ''}`}
          onClick={toggleBookmark}
          title={bookmarked ? t.research.bookmarkRemove : t.research.bookmarkSave}
        >
          {bookmarked ? '🔖' : '🏷️'}
        </button>
      </div>

      {/* Metrics Row */}
      <div className="article-metrics">
        {article.fwci && (
          <span className="metric">FWCI: {article.fwci.toFixed(2)}</span>
        )}
        {article.cite_score && (
          <span className="metric">CiteScore: {article.cite_score.toFixed(1)}</span>
        )}
        {article.sjr && (
          <span className="metric">SJR: {article.sjr.toFixed(2)}</span>
        )}
        {article.publication_types?.length > 0 && (
          <span className="metric type">{article.publication_types[0]}</span>
        )}
      </div>

      {/* Expandable Abstract */}
      {article.abstract && (
        <div className="article-abstract-section">
          <button className="abstract-toggle" onClick={() => setExpanded(!expanded)}>
            {expanded ? t.research.hideAbstract : t.research.showAbstract}
          </button>
          {expanded && (
            <div className="article-abstract">
              <p>{article.abstract}</p>
            </div>
          )}
        </div>
      )}

      {/* Confidence Breakdown */}
      {expanded && article.confidence_breakdown && Object.keys(article.confidence_breakdown).length > 0 && (
        <div className="confidence-breakdown">
          <h4>{t.research.scoreBreakdown}</h4>
          <div className="breakdown-bars">
            {Object.entries(article.confidence_breakdown).map(([key, value]) => (
              <div key={key} className="breakdown-row">
                <span className="breakdown-label">{key.replace(/_/g, ' ')}</span>
                <div className="breakdown-bar-track">
                  <div className="breakdown-bar-fill" style={{ width: `${Math.min(100, value)}%` }} />
                </div>
                <span className="breakdown-value">{typeof value === 'number' ? value.toFixed(1) : value}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default Research;

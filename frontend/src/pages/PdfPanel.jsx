/**
 * PdfPanel — O8: PDF Preview Side Panel
 *
 * Renders an embedded PDF viewer for a given source file and page number.
 * If PDF is not available for PubMed articles, displays the abstract in a markdown viewer.
 * Because the backend endpoint requires a JWT, the component fetches the PDF
 * as a Blob (with the Authorization header), creates an object URL, and points
 * the <iframe> at that URL.  The object URL is revoked when the panel closes.
 *
 * Props:
 *  source   {string}   The source path / filename returned in the agent response.
 *  page     {number}   The 1-based page number to navigate to (optional).
 *  onClose  {Function} Called when the user clicks the close button.
 *  apiUrl   {string}   Base URL of the backend (from config.API_URL).
 *  articleData {object} Optional pre-loaded article data to avoid redundant API calls.
 */
import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

function PdfPanel({ source, page, onClose, apiUrl, articleData: preloadedArticleData }) {
  const [blobUrl, setBlobUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(page || 1);
  const [showAbstract, setShowAbstract] = useState(false);
  const [articleData, setArticleData] = useState(preloadedArticleData || null);
  const [panelWidth, setPanelWidth] = useState(420);
  const [isResizing, setIsResizing] = useState(false);
  const prevBlobRef = useRef(null);
  const panelRef = useRef(null);

  // Extract PMID from source URL if it's a PubMed article
  const pmidMatch = source?.match(/\/pubmed\/pdf\/(\d+)/);
  const pmid = pmidMatch ? pmidMatch[1] : null;

  // If we have preloaded article data, show abstract immediately
  useEffect(() => {
    if (preloadedArticleData) {
      setArticleData(preloadedArticleData);
      setShowAbstract(true);
      setLoading(false);
    }
  }, [preloadedArticleData]);

  // Fetch PDF blob whenever the source changes
  useEffect(() => {
    if (!source || preloadedArticleData) return; // Skip if we have preloaded data

    let cancelled = false;
    setLoading(true);
    setError(null);
    setShowAbstract(false);
    setArticleData(null);

    const token = localStorage.getItem('token');
    
    // Handle both direct URLs (e.g., /api/pubmed/pdf/12345) and legacy paths
    let url;
    if (source.startsWith('http://') || source.startsWith('https://') || source.startsWith('/api/')) {
      // Direct URL - use as-is (prepend apiUrl if it's a relative path)
      url = source.startsWith('/') ? `${apiUrl}${source}` : source;
    } else {
      // Legacy path format - use old /api/pdf/serve endpoint
      url = `${apiUrl}/api/pdf/serve?source=${encodeURIComponent(source)}`;
    }

    fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (!res.ok) {
          // If PDF not available and it's a PubMed article, try to fetch abstract
          if (res.status === 404 && pmid) {
            return res.json().then(errorData => {
              throw { isPubMedError: true, status: 404, data: errorData };
            });
          }
          throw new Error(`Failed to load PDF (${res.status} ${res.statusText})`);
        }
        return res.blob();
      })
      .then((blob) => {
        if (cancelled) return;
        // Revoke any previous object URL to avoid memory leaks
        if (prevBlobRef.current) {
          URL.revokeObjectURL(prevBlobRef.current);
        }
        const objUrl = URL.createObjectURL(blob);
        prevBlobRef.current = objUrl;
        setBlobUrl(objUrl);
        setLoading(false);
      })
      .catch((err) => {
        if (cancelled) return;
        
        // If it's a PubMed article and PDF failed, fetch abstract
        if (err.isPubMedError && pmid) {
          fetch(`${apiUrl}/api/pubmed/article/${pmid}`, {
            headers: { Authorization: `Bearer ${token}` },
          })
            .then(res => res.json())
            .then(data => {
              if (!cancelled) {
                setArticleData(data);
                setShowAbstract(true);
                setLoading(false);
              }
            })
            .catch(() => {
              if (!cancelled) {
                setError(err.data?.detail?.message || err.message || 'Failed to load PDF');
                setLoading(false);
              }
            });
        } else {
          setError(err.message || 'Failed to load PDF');
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [source, apiUrl, pmid, preloadedArticleData]);

  // Sync currentPage when the prop changes (e.g. user clicks a different source)
  useEffect(() => {
    setCurrentPage(page || 1);
  }, [page, source]);

  // Cleanup object URL on unmount
  useEffect(() => {
    return () => {
      if (prevBlobRef.current) {
        URL.revokeObjectURL(prevBlobRef.current);
      }
    };
  }, []);

  // Handle panel resizing
  useEffect(() => {
    if (!isResizing) return;

    const handleMouseMove = (e) => {
      if (!panelRef.current) return;
      const containerRect = panelRef.current.parentElement.getBoundingClientRect();
      const newWidth = containerRect.right - e.clientX;
      // Constrain width between 320px and 80% of viewport
      const minWidth = 320;
      const maxWidth = window.innerWidth * 0.8;
      setPanelWidth(Math.max(minWidth, Math.min(maxWidth, newWidth)));
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing]);

  // The PDF.js viewer built into Firefox / Chromium supports the #page= fragment.
  const iframeSrc = blobUrl ? `${blobUrl}#page=${currentPage}` : null;

  // Extract a displayable filename from the source path or URL
  const displayName = source 
    ? source.includes('/pubmed/pdf/')
      ? `PubMed Article ${source.match(/\/(\d+)/)?.[1] || ''}`
      : source.split(/[\\/]/).pop()
    : 'Document';

  return (
    <div className="pdf-panel" ref={panelRef} style={{ width: `${panelWidth}px` }}>
      {/* Resize handle */}
      <div
        className="pdf-panel-resize-handle"
        onMouseDown={() => setIsResizing(true)}
        title="Drag to resize"
      />
      
      {/* ── Header ── */}
      <div className="pdf-panel-header">
        <div className="pdf-panel-title">
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
            <polyline points="10 9 9 9 8 9" />
          </svg>
          <span title={source}>{displayName}</span>
        </div>

        {/* Page navigation - only show for PDFs */}
        {!showAbstract && (
          <div className="pdf-panel-nav">
            <button
              className="pdf-nav-btn"
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={loading || currentPage <= 1}
              title="Previous page"
            >
              ‹
            </button>
            <span className="pdf-page-indicator">p. {currentPage}</span>
            <button
              className="pdf-nav-btn"
              onClick={() => setCurrentPage((p) => p + 1)}
              disabled={loading}
              title="Next page"
            >
              ›
            </button>
          </div>
        )}

        <button className="pdf-close-btn" onClick={onClose} title="Close panel">
          ✕
        </button>
      </div>

      {/* ── Body ── */}
      <div className="pdf-panel-body">
        {loading && (
          <div className="pdf-loading">
            <div className="pdf-spinner" />
            <span>Loading document…</span>
          </div>
        )}
        {error && (
          <div className="pdf-error">
            <svg
              width="32"
              height="32"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <p>{error}</p>
            <p className="pdf-error-hint">
              Ensure the PDF exists in the document store and you are logged in.
            </p>
          </div>
        )}
        {!loading && !error && showAbstract && articleData && (
          <div className="abstract-viewer">
            <div className="abstract-header">
              <h2>{articleData.title}</h2>
              <div className="abstract-meta">
                {articleData.authors && articleData.authors.length > 0 && (
                  <p className="abstract-authors">
                    {articleData.authors.slice(0, 5).join(', ')}
                    {articleData.authors.length > 5 && ' et al.'}
                  </p>
                )}
                {articleData.journal && (
                  <p className="abstract-journal">
                    <strong>{articleData.journal}</strong>
                    {articleData.publication_date && ` (${articleData.publication_date})`}
                  </p>
                )}
                {articleData.citation_count > 0 && (
                  <p className="abstract-citations">
                    📊 {articleData.citation_count} citations
                  </p>
                )}
              </div>
            </div>
            
            <div className="abstract-content">
              <h3>Abstract</h3>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {articleData.abstract || 'No abstract available.'}
              </ReactMarkdown>
            </div>

            <div className="abstract-links">
              {articleData.pubmed_url && (
                <a
                  href={articleData.pubmed_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="abstract-link-btn"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                    <polyline points="15 3 21 3 21 9" />
                    <line x1="10" y1="14" x2="21" y2="3" />
                  </svg>
                  View on PubMed
                </a>
              )}
              {articleData.doi_url && (
                <a
                  href={articleData.doi_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="abstract-link-btn"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                    <polyline points="15 3 21 3 21 9" />
                    <line x1="10" y1="14" x2="21" y2="3" />
                  </svg>
                  View via DOI
                </a>
              )}
            </div>

            <div className="abstract-notice">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="16" x2="12" y2="12" />
                <line x1="12" y1="8" x2="12.01" y2="8" />
              </svg>
              <span>Full-text PDF not available. Showing abstract only.</span>
            </div>
          </div>
        )}
        {!loading && !error && !showAbstract && iframeSrc && (
          <iframe
            key={iframeSrc}          /* re-mount when URL changes to force navigation */
            src={iframeSrc}
            title={`PDF preview — ${displayName}`}
            className="pdf-iframe"
          />
        )}
      </div>
    </div>
  );
}

export default PdfPanel;

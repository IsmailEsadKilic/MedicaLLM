/**
 * PdfPanel — O8: PDF Preview Side Panel
 *
 * Renders an embedded PDF viewer for a given source file and page number.
 * Because the backend endpoint requires a JWT, the component fetches the PDF
 * as a Blob (with the Authorization header), creates an object URL, and points
 * the <iframe> at that URL.  The object URL is revoked when the panel closes.
 *
 * Props:
 *  source   {string}   The source path / filename returned in the agent response.
 *  page     {number}   The 1-based page number to navigate to (optional).
 *  onClose  {Function} Called when the user clicks the close button.
 *  apiUrl   {string}   Base URL of the backend (from config.API_URL).
 */
import { useState, useEffect, useRef } from 'react';

function PdfPanel({ source, page, onClose, apiUrl }) {
  const [blobUrl, setBlobUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(page || 1);
  const prevBlobRef = useRef(null);

  // Fetch PDF blob whenever the source changes
  useEffect(() => {
    if (!source) return;

    let cancelled = false;
    setLoading(true);
    setError(null);

    const token = localStorage.getItem('token');
    const url = `${apiUrl}/api/pdf/serve?source=${encodeURIComponent(source)}`;

    fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (!res.ok) {
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
        if (!cancelled) {
          setError(err.message || 'Failed to load PDF');
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [source, apiUrl]);

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

  // The PDF.js viewer built into Firefox / Chromium supports the #page= fragment.
  const iframeSrc = blobUrl ? `${blobUrl}#page=${currentPage}` : null;

  // Extract a displayable filename from the source path
  const displayName = source ? source.split(/[\\/]/).pop() : 'Document';

  return (
    <div className="pdf-panel">
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

        {/* Page navigation */}
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
        {!loading && !error && iframeSrc && (
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

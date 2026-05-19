import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

/**
 * Markdown renderer with professional inline citation support.
 *
 * Audit S10: we removed `rehype-raw` from the rehype plugin chain. With
 * `rehype-raw` enabled, any raw HTML the LLM emitted (or that found its
 * way into a Markdown document via prompt injection) was rendered as live
 * HTML — a classic XSS vector. `react-markdown` defaults to escaping HTML,
 * which is what we want for any model-generated content.
 *
 * Accepts two citation formats from the LLM and renders them as IEEE-style
 * superscript badges that are clickable and scroll/link to the source:
 *   - [1], [2, 3], [1][2]  (preferred, compact)
 *   - [REF1], [REF2]       (legacy)
 *
 * Each rendered badge:
 *   - Shows just the number (e.g. ¹, ²) as a small pill
 *   - Displays a rich tooltip on hover (title, journal, type)
 *   - On click: scrolls to the matching source card and highlights it
 */
function MarkdownWithReferences({ content, sources, onSourceClick }) {
  // Build a map of ref number (int) -> source
  const sourceMap = {};
  if (sources && Array.isArray(sources)) {
    sources.forEach((source, idx) => {
      const refStr = source.ref || `REF${idx + 1}`;
      const m = String(refStr).match(/(\d+)/);
      const refNum = m ? parseInt(m[1], 10) : idx + 1;
      sourceMap[refNum] = { ...source, index: idx };
    });
  }

  // Regex: captures [1], [1, 2, 3], [REF1], [1][2] (consecutive handled by
  // splitting each bracket group independently).
  // Also handles full-width brackets 【1】 as a defensive measure.
  // Any bracket with one-or-more numbers (optionally prefixed "REF", comma-separated).
  const CITATION_RE = /[\[【](?:REF)?\s*(\d+(?:\s*,\s*(?:REF)?\s*\d+)*)\s*[\]】]/gi;

  function renderCitationTokens(match) {
    // match is the raw bracket text, e.g. "[1, 2]" or "[REF3]"
    const inner = match.replace(/[[\]REFref\s]/g, '');
    const nums = inner
      .split(',')
      .map((s) => parseInt(s, 10))
      .filter((n) => !Number.isNaN(n));

    return nums.map((n, i) => {
      const source = sourceMap[n];
      const title = source ? buildTooltip(source) : `Source ${n} (not found)`;
      const label = (
        <span className="ref-badge-inner">{n}</span>
      );
      if (source) {
        return (
          <button
            key={`cite-${n}-${i}`}
            type="button"
            className="inline-reference-btn"
            onClick={(e) => {
              e.stopPropagation();
              onSourceClick?.(source, source.index);
            }}
            title={title}
            aria-label={`Citation ${n}: ${source.title || 'source'}`}
          >
            {label}
          </button>
        );
      }
      // Unknown reference — render as dimmed badge, non-interactive
      return (
        <span
          key={`cite-missing-${n}-${i}`}
          className="inline-reference-btn inline-reference-btn--missing"
          title={`Reference ${n} not available`}
        >
          {label}
        </span>
      );
    });
  }

  function processTextWithReferences(children) {
    if (!children) return children;

    const childArray = React.Children.toArray(children);

    return childArray.map((child, idx) => {
      if (typeof child !== 'string') {
        return child;
      }

      const out = [];
      let lastIndex = 0;
      let match;

      // Reset regex state for each string
      CITATION_RE.lastIndex = 0;
      while ((match = CITATION_RE.exec(child)) !== null) {
        if (match.index > lastIndex) {
          out.push(
            <React.Fragment key={`t-${idx}-${lastIndex}`}>
              {child.substring(lastIndex, match.index)}
            </React.Fragment>
          );
        }
        const citations = renderCitationTokens(match[0]);
        out.push(
          <span
            key={`c-${idx}-${match.index}`}
            className="inline-reference-group"
          >
            {citations}
          </span>
        );
        lastIndex = match.index + match[0].length;
      }
      if (lastIndex < child.length) {
        out.push(
          <React.Fragment key={`t-${idx}-${lastIndex}`}>
            {child.substring(lastIndex)}
          </React.Fragment>
        );
      }
      return out;
    });
  }

  const components = {
    p: ({ children, ...props }) => (
      <p {...props}>{processTextWithReferences(children)}</p>
    ),
    li: ({ children, ...props }) => (
      <li {...props}>{processTextWithReferences(children)}</li>
    ),
    td: ({ children, ...props }) => (
      <td {...props}>{processTextWithReferences(children)}</td>
    ),
    th: ({ children, ...props }) => (
      <th {...props}>{processTextWithReferences(children)}</th>
    ),
    strong: ({ children, ...props }) => (
      <strong {...props}>{processTextWithReferences(children)}</strong>
    ),
    em: ({ children, ...props }) => (
      <em {...props}>{processTextWithReferences(children)}</em>
    ),
  };

  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={components}
    >
      {content}
    </ReactMarkdown>
  );
}

function buildTooltip(source) {
  const parts = [];
  if (source.title) parts.push(source.title);
  const meta = [];
  if (source.journal) meta.push(source.journal);
  if (source.publication_date) meta.push(source.publication_date.slice(0, 4));
  if (source.source_type === 'database' || source.source === 'DrugBank') {
    meta.push('DrugBank');
  } else if (source.pmid) {
    meta.push(`PMID ${source.pmid}`);
  }
  if (meta.length) parts.push(`— ${meta.join(' · ')}`);
  return parts.join(' ');
}

export default MarkdownWithReferences;

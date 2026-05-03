import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';

/**
 * Markdown renderer with inline reference support.
 * 
 * Converts [REF1], [REF2], etc. into clickable buttons that:
 * - Scroll to the source in the sources list
 * - Open PDFs in the side panel
 * - Link to PubMed articles
 */
function MarkdownWithReferences({ content, sources, onSourceClick }) {
  // Build a map of ref_id -> source for quick lookup
  const sourceMap = {};
  if (sources && Array.isArray(sources)) {
    sources.forEach((source, idx) => {
      const refId = source.ref || `REF${idx + 1}`;
      sourceMap[refId] = { ...source, index: idx };
    });
  }

  // Custom renderer for text nodes to replace [REF#] with clickable buttons
  const components = {
    p: ({ children, ...props }) => {
      return <p {...props}>{processTextWithReferences(children)}</p>;
    },
    li: ({ children, ...props }) => {
      return <li {...props}>{processTextWithReferences(children)}</li>;
    },
    // Process table cells
    td: ({ children, ...props }) => {
      return <td {...props}>{processTextWithReferences(children)}</td>;
    },
    th: ({ children, ...props }) => {
      return <th {...props}>{processTextWithReferences(children)}</th>;
    },
    // Process other text-containing elements as needed
    strong: ({ children, ...props }) => {
      return <strong {...props}>{processTextWithReferences(children)}</strong>;
    },
    em: ({ children, ...props }) => {
      return <em {...props}>{processTextWithReferences(children)}</em>;
    },
  };

  function processTextWithReferences(children) {
    if (!children) return children;

    // Convert children to array if it's not already
    const childArray = React.Children.toArray(children);

    return childArray.map((child, idx) => {
      // Only process string children
      if (typeof child !== 'string') {
        return child;
      }

      // Split text by [REF#] pattern
      const parts = child.split(/(\[REF\d+\])/g);

      return parts.map((part, partIdx) => {
        const refMatch = part.match(/\[REF(\d+)\]/);

        if (refMatch) {
          const refNum = refMatch[1];
          const refId = `REF${refNum}`;
          const source = sourceMap[refId];

          if (source) {
            return (
              <button
                key={`${idx}-${partIdx}`}
                className="inline-reference-btn"
                onClick={() => onSourceClick(source, source.index)}
                title={source.title || 'View source'}
              >
                [{refNum}]
              </button>
            );
          }
        }

        return <React.Fragment key={`${idx}-${partIdx}`}>{part}</React.Fragment>;
      });
    });
  }

  return (
    <ReactMarkdown 
      remarkPlugins={[remarkGfm]} 
      rehypePlugins={[rehypeRaw]}
      components={components}
    >
      {content}
    </ReactMarkdown>
  );
}

export default MarkdownWithReferences;

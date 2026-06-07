import React from 'react';
import './LoadingScreen.css';

/**
 * Branded loading state used across the app.
 *
 * Two variants:
 *   - default (full-screen): pulse logo + spinner + tagline. Use when the
 *     whole page is bootstrapping (e.g. after login while conversations
 *     are fetched).
 *   - inline: a smaller dot-spinner sized for in-panel placeholders such
 *     as "Loading patients..." inside the doctor pages.
 *
 * The SVG mark is a stylised stethoscope/heart pulse drawn in the navy
 * accent so users see "their" brand instead of a generic spinner.
 */
function LoadingScreen({
  message = 'Loading',
  variant = 'fullscreen',
  className = '',
}) {
  if (variant === 'inline') {
    return (
      <div className={`loading-inline ${className}`}>
        <span className="loading-inline-dots" aria-hidden="true">
          <span />
          <span />
          <span />
        </span>
        <span className="loading-inline-label">{message}</span>
      </div>
    );
  }

  return (
    <div className={`loading-screen ${className}`} role="status" aria-live="polite">
      <div className="loading-screen-stage">
        <div className="loading-screen-pulse-wrap">
          <span className="loading-screen-pulse-ring" />
          <span className="loading-screen-pulse-ring loading-screen-pulse-ring--delayed" />
          <svg
            className="loading-screen-mark"
            width="56"
            height="56"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            {/* Stethoscope arc */}
            <path d="M4.8 2.3A.3.3 0 1 0 5 2H4a2 2 0 0 0-2 2v5a6 6 0 0 0 6 6 6 6 0 0 0 6-6V4a2 2 0 0 0-2-2h-1a.2.2 0 1 0 .3.3" />
            {/* Pulse line */}
            <path d="M8 15v2a4 4 0 0 0 4 4 4 4 0 0 0 4-4v-1" />
            {/* Bell */}
            <circle cx="20" cy="10" r="2" />
          </svg>
        </div>

        <div className="loading-screen-text">
          <span className="loading-screen-title">{message}</span>
          <span className="loading-screen-dots" aria-hidden="true">
            <span>.</span>
            <span>.</span>
            <span>.</span>
          </span>
        </div>
      </div>
    </div>
  );
}

export default LoadingScreen;

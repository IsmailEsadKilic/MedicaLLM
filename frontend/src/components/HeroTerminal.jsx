import React, { useEffect, useRef, useState } from 'react';

/**
 * Animated chat terminal for the landing hero.
 *
 * Cycles through a list of question/answer pairs, typing each line out
 * character by character, pausing between phases, then clearing and
 * moving to the next conversation. Pure JS — no external animation
 * library — so the bundle stays tiny.
 *
 * Props
 * -----
 * conversations  Array of { question, thinking?, answer: { pre, strong, post } }
 * labels         { you, ai } — translated labels for the speaker tags
 * zapIcon        ReactNode rendered next to the "thinking" line
 *
 * Respects prefers-reduced-motion: skips the animation and just shows
 * the first conversation rendered fully.
 */
export default function HeroTerminal({ conversations, labels, zapIcon }) {
  // Index of the conversation currently on stage.
  const [convIdx, setConvIdx] = useState(0);
  // Phase determines what's currently visible / animating.
  //   'q'      — typing the user question
  //   'q-done' — question fully shown, brief pause
  //   't'      — typing the "Searching…" thinking line
  //   't-done' — thinking line shown, brief pause
  //   'a'      — typing the assistant answer (pre + strong + post)
  //   'a-done' — full answer shown, hold before clearing
  const [phase, setPhase] = useState('q');
  const [typed, setTyped] = useState({ q: '', t: '', aPre: '', aStrong: '', aPost: '' });

  // Allow the user OS preference to disable the animation entirely.
  const reducedMotion = useRef(
    typeof window !== 'undefined' &&
      window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches,
  );

  // Reset typed state whenever the active conversation changes.
  useEffect(() => {
    setTyped({ q: '', t: '', aPre: '', aStrong: '', aPost: '' });
    setPhase('q');
  }, [convIdx]);

  useEffect(() => {
    if (!conversations?.length) return;
    if (reducedMotion.current) {
      // Show the first conversation fully without animation.
      const c = conversations[0];
      setTyped({
        q: c.question,
        t: c.thinking || '',
        aPre: c.answer.pre,
        aStrong: c.answer.strong,
        aPost: c.answer.post,
      });
      setPhase('a-done');
      return;
    }

    const conv = conversations[convIdx % conversations.length];
    const TYPE_MS = 22;       // per-character speed
    const PAUSE_AFTER = 600;  // pause between phases
    const HOLD_FINAL = 2400;  // dwell on the completed answer
    let cancelled = false;
    let timer;

    function typeInto(field, fullText, onDone) {
      let i = 0;
      const tick = () => {
        if (cancelled) return;
        i += 1;
        setTyped((prev) => ({ ...prev, [field]: fullText.slice(0, i) }));
        if (i < fullText.length) {
          timer = setTimeout(tick, TYPE_MS);
        } else {
          timer = setTimeout(onDone, PAUSE_AFTER);
        }
      };
      if (!fullText) {
        // Skip empty phases (e.g. conversations without a thinking line).
        timer = setTimeout(onDone, 0);
        return;
      }
      timer = setTimeout(tick, TYPE_MS);
    }

    if (phase === 'q') {
      typeInto('q', conv.question, () => setPhase('t'));
    } else if (phase === 't') {
      typeInto('t', conv.thinking || '', () => setPhase('a-pre'));
    } else if (phase === 'a-pre') {
      typeInto('aPre', conv.answer.pre, () => setPhase('a-strong'));
    } else if (phase === 'a-strong') {
      typeInto('aStrong', conv.answer.strong, () => setPhase('a-post'));
    } else if (phase === 'a-post') {
      typeInto('aPost', conv.answer.post, () => setPhase('a-done'));
    } else if (phase === 'a-done') {
      timer = setTimeout(() => {
        if (cancelled) return;
        setConvIdx((i) => (i + 1) % conversations.length);
      }, HOLD_FINAL);
    }

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [phase, convIdx, conversations]);

  if (!conversations?.length) return null;

  const showQuestion = typed.q.length > 0;
  const showThinking = typed.t.length > 0;
  const showAnswer = typed.aPre.length > 0;

  // Cursor only shows on the line currently being typed — keeps the
  // illusion of one writer working through the conversation.
  const cursorOnQ = phase === 'q';
  const cursorOnT = phase === 't';
  const cursorOnAnswer = phase === 'a-pre' || phase === 'a-strong' || phase === 'a-post';

  return (
    <div className="terminal-mock">
      <div className="terminal-bar"><span /><span /><span /></div>
      <div className="terminal-body">
        {showQuestion && (
          <p className="t-user">
            <span className="t-label">{labels.you}</span>{' '}
            {typed.q}
            {cursorOnQ && <span className="terminal-cursor" aria-hidden="true">|</span>}
          </p>
        )}
        {showThinking && (
          <p className="t-ai-alt">
            {zapIcon} {typed.t}
            {cursorOnT && <span className="terminal-cursor" aria-hidden="true">|</span>}
          </p>
        )}
        {showAnswer && (
          <p className="t-ai">
            <span className="t-label">{labels.ai}</span>{' '}
            {typed.aPre}
            {typed.aStrong && <strong>{typed.aStrong}</strong>}
            {typed.aPost}
            {cursorOnAnswer && <span className="terminal-cursor" aria-hidden="true">|</span>}
          </p>
        )}
      </div>
    </div>
  );
}

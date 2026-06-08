/**
 * Translation parity tests.
 *
 * Goal: every key that exists in the English tree exists in Turkish, and
 * vice versa. Without this, a missing translation silently falls back to
 * English and we ship half-translated screens.
 *
 * The shape of each strings module is `{ en: {...}, tr: {...} }` — a
 * recursive walk + set comparison catches both missing keys and accidental
 * structural drift (e.g. someone changes a string into an object on one
 * side only).
 */
import { describe, expect, test } from 'vitest';
import { CHAT_STRINGS } from '../chat';
import { ADMIN_STRINGS } from '../admin';
import { PATIENT_STRINGS } from '../patient';
import { DOCTOR_STRINGS } from '../doctor';
import { DRUG_MATRIX_STRINGS } from '../drugMatrix';

/** Recursively collect dot-paths of every leaf in an object tree. */
function collectKeys(obj, prefix = '') {
  const keys = [];
  for (const [k, v] of Object.entries(obj)) {
    const path = prefix ? `${prefix}.${k}` : k;
    if (v !== null && typeof v === 'object' && !Array.isArray(v) && typeof v !== 'function') {
      keys.push(...collectKeys(v, path));
    } else {
      keys.push(path);
    }
  }
  return keys.sort();
}

const MODULES = [
  ['CHAT_STRINGS', CHAT_STRINGS],
  ['ADMIN_STRINGS', ADMIN_STRINGS],
  ['PATIENT_STRINGS', PATIENT_STRINGS],
  ['DOCTOR_STRINGS', DOCTOR_STRINGS],
  ['DRUG_MATRIX_STRINGS', DRUG_MATRIX_STRINGS],
];

describe.each(MODULES)('%s — EN ↔ TR parity', (name, mod) => {
  test('both languages exist', () => {
    expect(mod.en).toBeTypeOf('object');
    expect(mod.tr).toBeTypeOf('object');
  });

  test('every EN key has a TR counterpart', () => {
    const en = collectKeys(mod.en);
    const tr = collectKeys(mod.tr);
    const missing = en.filter((k) => !tr.includes(k));
    expect(missing).toEqual([]);
  });

  test('every TR key has an EN counterpart', () => {
    const en = collectKeys(mod.en);
    const tr = collectKeys(mod.tr);
    const extra = tr.filter((k) => !en.includes(k));
    expect(extra).toEqual([]);
  });
});

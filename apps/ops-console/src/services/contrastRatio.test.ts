import { describe, expect, it } from 'vitest';

import { contrastRatio, wcagAAContrast } from './contrastRatio';

/**
 * Pinned hex pairs from the Phase 01 blueprint §2.3 (verified 2026-08-08):
 * `--fp-primary #dbe4ee`, `--fp-elevated #111a26`, `--fp-input #233040`,
 * `--fp-secondary #8fa1b3`, `--fp-muted #5b6b7d`, `--fp-placeholder #94a3b8`.
 * Tolerance ±0.05.
 */
const PINNED_PAIRS: ReadonlyArray<{
  fg: string;
  bg: string;
  expected: number;
}> = [
  { fg: '#dbe4ee', bg: '#111a26', expected: 13.62 }, // primary on elevated (AAA)
  { fg: '#dbe4ee', bg: '#233040', expected: 10.42 }, // primary on input (AA)
  { fg: '#8fa1b3', bg: '#111a26', expected: 6.6 }, // secondary on elevated (AA)
  { fg: '#8fa1b3', bg: '#233040', expected: 5.05 }, // secondary on input (AA)
  { fg: '#5b6b7d', bg: '#233040', expected: 2.45 }, // muted on input (documents exemption)
  { fg: '#94a3b8', bg: '#233040', expected: 5.22 }, // placeholder on input (AA)
];

const TOLERANCE = 0.05;

describe('contrastRatio', () => {
  it.each(PINNED_PAIRS.map(({ fg, bg, expected }) => [`${fg} on ${bg}`, fg, bg, expected]))(
    'pins %s at %f (±0.05)',
    (_label, fg, bg, expected) => {
      expect(contrastRatio(fg as string, bg as string)).toBeCloseTo(expected as number, 2);
      expect(Math.abs(contrastRatio(fg as string, bg as string) - (expected as number))).toBeLessThanOrEqual(
        TOLERANCE,
      );
    },
  );

  it('is order-independent', () => {
    expect(contrastRatio('#94a3b8', '#233040')).toBe(contrastRatio('#233040', '#94a3b8'));
  });

  it('returns 21 for black on white and 1 for identical colors', () => {
    expect(contrastRatio('#ffffff', '#000000')).toBe(21);
    expect(contrastRatio('#000000', '#000000')).toBe(1);
  });

  it('throws on malformed hex', () => {
    expect(() => contrastRatio('xyz', '#000000')).toThrow(TypeError);
    expect(() => contrastRatio('#12345', '#000000')).toThrow(TypeError);
    expect(() => contrastRatio('#gggggg', '#000000')).toThrow(TypeError);
  });
});

describe('wcagAAContrast', () => {
  it('passes the pinned AA pairs', () => {
    expect(wcagAAContrast('#dbe4ee', '#111a26')).toBe(true);
    expect(wcagAAContrast('#dbe4ee', '#233040')).toBe(true);
    expect(wcagAAContrast('#8fa1b3', '#233040')).toBe(true);
    expect(wcagAAContrast('#94a3b8', '#233040')).toBe(true); // placeholder at 5.22:1
  });

  it('fails the documented exempted pairs', () => {
    expect(wcagAAContrast('#5b6b7d', '#233040')).toBe(false); // muted 2.45:1
    expect(wcagAAContrast('#5b6b7d', '#111a26')).toBe(false); // muted 3.20:1 (TECH-78)
  });

  it('resolves the 4.5:1 boundary correctly', () => {
    expect(wcagAAContrast('#959595', '#233040')).toBe(false); // 4.4704:1 — just under
    expect(wcagAAContrast('#969696', '#233040')).toBe(true); // 4.5271:1 — just over
  });

  it('agrees with the contrastRatio threshold for every pinned pair', () => {
    for (const { fg, bg } of PINNED_PAIRS) {
      expect(wcagAAContrast(fg, bg)).toBe(contrastRatio(fg, bg) >= 4.5);
    }
  });
});

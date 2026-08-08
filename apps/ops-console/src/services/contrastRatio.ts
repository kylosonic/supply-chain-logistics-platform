/**
 * Pure WCAG 2.1 contrast utilities over hex color strings.
 *
 * No DOM, no framework, no dependencies — only Math over parsed channels.
 * Pinned against the design-system ratios recorded in
 * `docs/plans/phase-console-login-color-fidelity-01-token-surfaces.md` §2.3
 * by `contrastRatio.test.ts`; reused by the TECH-78 small-text audit.
 */

type Rgb = readonly [number, number, number];

function parseHex(hex: string): Rgb {
  const normalized = hex.trim().replace(/^#/, '');
  if (/^[0-9a-f]{3}$/i.test(normalized)) {
    const [r, g, b] = normalized.split('');
    return [parseInt(`${r}${r}`, 16), parseInt(`${g}${g}`, 16), parseInt(`${b}${b}`, 16)];
  }
  if (/^[0-9a-f]{6}$/i.test(normalized)) {
    return [
      parseInt(normalized.slice(0, 2), 16),
      parseInt(normalized.slice(2, 4), 16),
      parseInt(normalized.slice(4, 6), 16),
    ];
  }
  throw new TypeError(`Malformed hex color: ${hex}`);
}

function channelLuminance(value: number): number {
  const channel = value / 255;
  return channel <= 0.03928 ? channel / 12.92 : Math.pow((channel + 0.055) / 1.055, 2.4);
}

function relativeLuminance(hex: string): number {
  const [r, g, b] = parseHex(hex);
  return 0.2126 * channelLuminance(r) + 0.7152 * channelLuminance(g) + 0.0722 * channelLuminance(b);
}

/**
 * WCAG 2.1 contrast ratio between two hex colors (order-independent).
 * Throws `TypeError` on malformed hex input.
 */
export function contrastRatio(hexA: string, hexB: string): number {
  const luminanceA = relativeLuminance(hexA);
  const luminanceB = relativeLuminance(hexB);
  const lighter = Math.max(luminanceA, luminanceB);
  const darker = Math.min(luminanceA, luminanceB);
  return (lighter + 0.05) / (darker + 0.05);
}

/**
 * Whether `hexFg` on `hexBg` meets WCAG 2.1 AA for normal (small) text:
 * contrast ratio >= 4.5:1. The boundary itself (exactly 4.5) passes.
 */
export function wcagAAContrast(hexFg: string, hexBg: string): boolean {
  return contrastRatio(hexFg, hexBg) >= 4.5;
}

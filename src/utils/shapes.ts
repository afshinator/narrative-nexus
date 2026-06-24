/** Source outlet format → scatter plot marker shape.
 *  Modify mappings here to change scatter plot visual encoding. */

// Shape names correspond to D3 symbol types: circle, square, diamond, triangle, cross
export const TIER_SHAPE: Record<number, string> = {
  1: "circle",    // Wire / Consensus anchor
  2: "square",    // Mainstream editorial
  3: "diamond",   // International
  4: "triangle",  // Independent / Investigative
  5: "cross",     // Contrarian
} as const

export function getShapeForTier(tier: number): string {
  return TIER_SHAPE[tier] ?? "circle"
}

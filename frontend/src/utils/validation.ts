export const SLUG_PATTERN = /^[a-z0-9]+(?:-[a-z0-9]+)*$/
export const SECTION_KEY_PATTERN = /^[a-z0-9_]+$/
export const HEX_COLOR_PATTERN = /^#[0-9a-fA-F]{6}$/

export function isValidGenreSlug(value: string): boolean {
  return SLUG_PATTERN.test(value)
}

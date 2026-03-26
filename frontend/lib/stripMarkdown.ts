/**
 * Strip markdown syntax from text intended for plain-text display.
 * Removes headers (#), bold (**), italic (*_), links, images, code blocks.
 */
export function stripMarkdown(text: string): string {
  if (!text) return ''
  return text
    // Remove headers: "# Title" -> "Title"
    .replace(/^#{1,6}\s+/gm, '')
    // Remove bold: **text** or __text__ -> text
    .replace(/\*\*(.+?)\*\*/g, '$1')
    .replace(/__(.+?)__/g, '$1')
    // Remove italic: *text* or _text_ -> text
    .replace(/\*(.+?)\*/g, '$1')
    .replace(/_(.+?)_/g, '$1')
    // Remove inline code: `code` -> code
    .replace(/`(.+?)`/g, '$1')
    // Remove links: [text](url) -> text
    .replace(/\[(.+?)\]\(.+?\)/g, '$1')
    // Remove images: ![alt](url) -> alt
    .replace(/!\[(.+?)\]\(.+?\)/g, '$1')
    // Remove blockquotes: > text -> text
    .replace(/^>\s+/gm, '')
    // Remove horizontal rules
    .replace(/^---+$/gm, '')
    // Collapse multiple newlines
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

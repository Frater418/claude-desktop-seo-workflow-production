export function base64Text(value: string): string {
  try {
    return atob(value)
  } catch (error) {
    if (error instanceof DOMException) return ""
    throw error
  }
}

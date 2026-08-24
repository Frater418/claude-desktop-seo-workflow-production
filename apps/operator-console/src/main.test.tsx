import { afterEach, describe, expect, it, vi } from "vitest"

afterEach(() => {
  document.body.replaceChildren()
  const root = document.createElement("div")
  root.id = "root"
  document.body.append(root)
  vi.resetModules()
})

describe("Operator Console entrypoint", () => {
  it("reports a German fatal state when the application root is unavailable", async () => {
    document.body.replaceChildren()

    await expect(import("./main")).rejects.toThrow("Das Root-Element der Operator-Konsole fehlt.")
  })
})

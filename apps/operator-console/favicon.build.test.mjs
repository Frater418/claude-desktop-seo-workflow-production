import { access, mkdtemp, readFile, rm } from "node:fs/promises"
import { tmpdir } from "node:os"
import { join } from "node:path"
import { build } from "vite"
import { describe, expect, it } from "vitest"

describe("Operator Console favicon build", () => {
  it("emits the SVG favicon declared by the production document", async () => {
    const outputDirectory = await mkdtemp(join(tmpdir(), "operator-console-favicon-"))
    try {
      await build({ build: { outDir: outputDirectory }, logLevel: "silent" })

      const document = await readFile(join(outputDirectory, "index.html"), "utf8")
      expect(document).toContain('<link rel="icon" type="image/svg+xml" href="/favicon.svg" />')
      await access(join(outputDirectory, "favicon.svg"))
    } finally {
      await rm(outputDirectory, { force: true, recursive: true })
    }
  })
})

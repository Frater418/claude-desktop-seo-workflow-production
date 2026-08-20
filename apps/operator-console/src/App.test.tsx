import { afterEach, describe, expect, it, vi } from "vitest"
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react"
import { App } from "./App"

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe("Operator console modes", () => {
  it("uses local simulation only when the query is exactly mode=demo", async () => {
    render(<App search="?mode=demo" />)

    expect(screen.getByText("Local simulation")).toBeInTheDocument()
    expect(screen.getByText("Northwind Facilities rollout")).toBeInTheDocument()
  })

  it.each(["", "?mode=demo&x=1", "?x=1&mode=demo", "?mode=Demo", "?mode=demo&mode=demo"])(
    "does not enable simulation for %s",
    async (search) => {
      vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("connection refused")))

      render(<App search={search} />)

      await waitFor(() => {
        expect(screen.getByText("Real API unavailable")).toBeInTheDocument()
      })
      expect(screen.queryByText("Local simulation")).not.toBeInTheDocument()
    }
  )

  it("does not fall back to demo data when the real API is unavailable", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("connection refused")))

    render(<App search="" />)

    await waitFor(() => {
      expect(screen.getByText("Real API unavailable")).toBeInTheDocument()
    })
    expect(screen.queryByText("Local simulation")).not.toBeInTheDocument()
    expect(screen.queryByText("Northwind Facilities rollout")).not.toBeInTheDocument()
  })
})

describe("Workflow route and detail", () => {
  it("presents the exact initial route and keeps 3b as a post-publication sideflow", () => {
    render(<App search="?mode=demo" />)

    expect(screen.getByLabelText("Initial workflow route")).toHaveTextContent(
      "0 1 1b 1c 2 3 4a 4b"
    )
    expect(screen.getByLabelText("Post-publication sideflow")).toHaveTextContent("3b")
  })

  it("updates the selected step detail", () => {
    render(<App search="?mode=demo" />)

    fireEvent.click(screen.getByRole("button", { name: "Step 1b: Information architecture" }))

    expect(screen.getByRole("heading", { name: "Information architecture" })).toBeInTheDocument()
    expect(screen.getByText("Map the approved themes into a usable site structure.")).toBeInTheDocument()
  })

  it("keeps raw projection data inside a closed technical disclosure", () => {
    render(<App search="?mode=demo" />)

    const details = screen.getByText("Technical details").closest("details")
    expect(details).not.toHaveAttribute("open")

    fireEvent.click(screen.getByText("Technical details"))
    expect(details).toHaveAttribute("open")
    expect(screen.getByText("project-neutral-031")).toBeInTheDocument()
  })

  it("keeps blocked and locked human actions unavailable as previews", () => {
    render(<App search="?mode=demo" />)

    fireEvent.click(screen.getByRole("button", { name: "Step 1c: Template system" }))

    expect(screen.getByText("Blocked until the information architecture gate releases.")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Start step preview" })).toBeDisabled()
    expect(screen.getByRole("button", { name: "Approve gate preview" })).toBeDisabled()

    fireEvent.click(screen.getByRole("button", { name: "Step 3b: Performance check" }))

    expect(screen.getByRole("button", { name: "Start step preview" })).toBeDisabled()
    expect(screen.getByRole("button", { name: "Approve gate preview" })).toBeDisabled()
  })
})

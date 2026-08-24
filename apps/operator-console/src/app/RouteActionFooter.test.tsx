import { afterEach, describe, expect, it } from "vitest"
import { cleanup, render, screen } from "@testing-library/react"
import { RouteActionFooter, RouteActionFooterProvider, RouteActionFooterSlot } from "./RouteActionFooter"

afterEach(cleanup)

describe("RouteActionFooter", () => {
  it("renders inline when a focused workspace has no shell slot", () => {
    render(<RouteActionFooter><button type="button">Aktion ausfuehren</button></RouteActionFooter>)

    expect(screen.getByRole("contentinfo")).toHaveClass("route-action-footer")
    expect(screen.getByRole("button", { name: "Aktion ausfuehren" })).toBeInTheDocument()
  })

  it("portals actions into the shell footer outside the workspace scroll owner", () => {
    render(<RouteActionFooterProvider><div className="workspace-frame"><section className="workspace-main">Arbeitsbereich<RouteActionFooter><button type="button">Aktion ausfuehren</button></RouteActionFooter></section></div><RouteActionFooterSlot /></RouteActionFooterProvider>)

    const footer = screen.getByRole("contentinfo")
    expect(footer).toHaveClass("route-action-footer")
    expect(document.querySelector(".workspace-frame")?.contains(footer)).toBe(false)
    expect(footer).toContainElement(screen.getByRole("button", { name: "Aktion ausfuehren" }))
  })

  it("keeps an empty slot out of layout and places the portal action after the workspace in keyboard order", () => {
    render(<RouteActionFooterProvider><div className="workspace-frame"><button type="button">Arbeitsaktion</button></div><RouteActionFooterSlot /><RouteActionFooter><button type="button">Footeraktion</button></RouteActionFooter></RouteActionFooterProvider>)

    const workspaceAction = screen.getByRole("button", { name: "Arbeitsaktion" })
    const footerAction = screen.getByRole("button", { name: "Footeraktion" })
    footerAction.focus()
    expect(document.activeElement).toBe(footerAction)
    expect(workspaceAction.compareDocumentPosition(footerAction) & Node.DOCUMENT_POSITION_FOLLOWING).toBe(Node.DOCUMENT_POSITION_FOLLOWING)
    expect(document.querySelector(".route-action-footer-slot")?.children).toHaveLength(1)
  })
})

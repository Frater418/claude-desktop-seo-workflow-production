import { createContext, useContext, useState } from "react"
import { createPortal } from "react-dom"
import type { Dispatch, ReactNode, SetStateAction } from "react"

type RouteActionFooterContextValue = { readonly target: HTMLElement | null; readonly setTarget: Dispatch<SetStateAction<HTMLElement | null>> }

const RouteActionFooterContext = createContext<RouteActionFooterContextValue | null>(null)

export function RouteActionFooterProvider({ children }: { readonly children: ReactNode }): JSX.Element {
  const [target, setTarget] = useState<HTMLElement | null>(null)
  return <RouteActionFooterContext.Provider value={{ target, setTarget }}>{children}</RouteActionFooterContext.Provider>
}

export function RouteActionFooterSlot(): JSX.Element {
  const context = useContext(RouteActionFooterContext)
  if (context === null) throw new Error("RouteActionFooterSlot requires RouteActionFooterProvider.")
  return <div className="route-action-footer-slot" ref={context.setTarget} />
}

export function RouteActionFooter({ children }: { readonly children: ReactNode }): JSX.Element {
  const target = useContext(RouteActionFooterContext)?.target ?? null
  const footer = <footer className="route-action-footer">{children}</footer>
  return target === null ? footer : createPortal(footer, target)
}

export type OperatorApiErrorOptions = { readonly kind: "http" | "network" | "unparseable"; readonly status: number; readonly message: string; readonly code?: string }

export class OperatorApiError extends Error {
  public readonly kind: OperatorApiErrorOptions["kind"]
  public readonly status: number
  public readonly code?: string

  public constructor(options: OperatorApiErrorOptions) {
    super(options.message)
    this.name = "OperatorApiError"
    this.kind = options.kind
    this.status = options.status
    if (options.code !== undefined) this.code = options.code
  }
}

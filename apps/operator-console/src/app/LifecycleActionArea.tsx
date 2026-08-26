import type { ActionIntent } from "../generated/api-types"
import { PersistentActionArea } from "./PersistentActionArea"
import { useAdminAction, type AdminActionClient } from "./useAdminAction"

type LifecycleActionAreaProps = {
  readonly client: AdminActionClient
  readonly intent: ActionIntent
  readonly title: string
  readonly description: string
  readonly previewLabel: string
  readonly confirmLabel: string
  readonly completedLabel: string
  readonly reload: () => Promise<void>
}

export function LifecycleActionArea({ client, intent, title, description, previewLabel, confirmLabel, completedLabel, reload }: LifecycleActionAreaProps): JSX.Element {
  const action = useAdminAction({ client, reload })
  return <PersistentActionArea
    title={title}
    description={description}
    previewLabel={previewLabel}
    confirmLabel={confirmLabel}
    completedLabel={completedLabel}
    state={action.state}
    onPreview={() => { void action.preview(intent) }}
    onConfirm={() => { void action.confirm() }}
  />
}

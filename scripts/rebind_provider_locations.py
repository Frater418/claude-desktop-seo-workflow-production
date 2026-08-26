#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from services.operator_api.clock import SystemClock
from services.operator_api.provider_location_upgrade import (
    ProviderLocationUpgradeError,
    ProviderLocationUpgradeService,
)
from services.operator_api.repository import ProjectRepository, WorkspaceRegistration, WorkspaceRegistry


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Preview or apply briefing-derived provider location bindings to an existing Project V2."
    )
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--tenant-id", required=True)
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--actor-id", default="operator-heartweb-admin")
    parser.add_argument("--idempotency-key")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    workspace = args.workspace.resolve(strict=True)
    repository_root = args.repository_root.resolve(strict=True)
    repository = ProjectRepository(
        WorkspaceRegistry((WorkspaceRegistration(args.tenant_id, args.project_id, workspace),))
    )
    service = ProviderLocationUpgradeService(repository, repository_root, SystemClock())
    try:
        preview = service.preview(args.tenant_id, args.project_id)
        result = preview.public()
        if args.apply:
            if not isinstance(args.idempotency_key, str) or len(args.idempotency_key) < 12:
                raise ProviderLocationUpgradeError(
                    "ERROR_CONTEXT_SCHEMA_INVALID",
                    "--apply requires an explicit --idempotency-key with at least 12 characters.",
                )
            result = service.apply(
                args.tenant_id,
                args.project_id,
                preview_hash=preview.preview_hash,
                expected_project_sha256=preview.current_project_sha256,
                actor_id=args.actor_id,
                idempotency_key=args.idempotency_key,
                confirmed=True,
            )
        print(json.dumps({"ok": True, "applied": args.apply, "data": result}, ensure_ascii=False, sort_keys=True))
        return 0
    except ProviderLocationUpgradeError as error:
        print(json.dumps({"ok": False, "code": error.code, "message": error.message}, ensure_ascii=False, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

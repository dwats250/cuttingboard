#!/usr/bin/env bash
# Wrapper for `npx gitnexus analyze` that prevents automatic injection of the
# GitNexus block into CLAUDE.md. Use this instead of running gitnexus analyze
# directly. CLAUDE.md is maintained manually; the injected block is a duplicate.
set -euo pipefail
exec npx gitnexus analyze --skip-agents-md "$@"

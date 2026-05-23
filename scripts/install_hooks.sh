#!/usr/bin/env bash
# Install local git hooks for this repository.
#
# Git hooks live under .git/hooks which is not tracked, so this script
# materializes the canonical hooks from tracked scripts. Re-run after
# cloning, or after editing scripts/pre_commit_sanity.sh, to refresh
# the installed hook.
#
# To bypass any installed hook for a single commit: `git commit --no-verify`.
set -euo pipefail

REPO_ROOT=$(git rev-parse --show-toplevel)
HOOKS_DIR="$REPO_ROOT/.git/hooks"

mkdir -p "$HOOKS_DIR"

cat > "$HOOKS_DIR/pre-commit" <<'EOF'
#!/usr/bin/env bash
# Installed by scripts/install_hooks.sh. Runs the canonical
# pre-commit sanity script. Informational only — does not block
# commits. To bypass: `git commit --no-verify`.
exec scripts/pre_commit_sanity.sh
EOF
chmod +x "$HOOKS_DIR/pre-commit"

echo "installed: $HOOKS_DIR/pre-commit -> scripts/pre_commit_sanity.sh"

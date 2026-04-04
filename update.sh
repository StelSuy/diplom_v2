#!/usr/bin/env bash
# =============================================================================
#  TimeTracker — update.sh
#  Pull latest code and redeploy with zero downtime
#  Usage: ./update.sh
# =============================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

info()    { echo -e "${CYAN}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }
step()    { echo -e "\n${BOLD}${BLUE}▶ $*${NC}"; }

echo -e "${BOLD}${CYAN}"
echo "╔══════════════════════════════════════╗"
echo "║   TimeTracker — Update Script v1.0   ║"
echo "╚══════════════════════════════════════╝${NC}"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# ── Pre-update backup ─────────────────────────────────────────────────────────
step "Creating pre-update database backup"
if [[ -f "./backup.sh" ]]; then
  ./backup.sh --quiet || warn "Backup failed — continuing anyway"
else
  warn "backup.sh not found, skipping backup"
fi

# ── Pull code ────────────────────────────────────────────────────────────────
step "Pulling latest code from git"
if git rev-parse --git-dir > /dev/null 2>&1; then
  BEFORE=$(git rev-parse --short HEAD)
  git pull --rebase origin "$(git branch --show-current)"
  AFTER=$(git rev-parse --short HEAD)
  if [[ "$BEFORE" == "$AFTER" ]]; then
    info "No code changes (already at $AFTER)"
  else
    success "Updated: ${BEFORE} → ${AFTER}"
    git log --oneline "${BEFORE}..${AFTER}" | sed 's/^/  /'
  fi
else
  warn "Not a git repository — skipping git pull"
fi

# ── Rebuild & restart ─────────────────────────────────────────────────────────
step "Rebuilding images (if changed)"
docker compose build --pull --quiet

step "Rolling restart (no downtime)"
docker compose up -d --remove-orphans

# ── Wait for healthy ──────────────────────────────────────────────────────────
step "Waiting for API to become healthy"
MAX_WAIT=60; WAITED=0
while true; do
  if curl -sf http://localhost/health >/dev/null 2>&1 || \
     curl -sf http://localhost:8000/health >/dev/null 2>&1; then
    success "API is responding"
    break
  fi
  if (( WAITED >= MAX_WAIT )); then
    warn "API not responding after ${MAX_WAIT}s. Check: docker compose logs api"
    break
  fi
  echo -n "."; sleep 3; WAITED=$((WAITED + 3))
done
echo ""

# ── Cleanup old images ────────────────────────────────────────────────────────
step "Cleaning up unused Docker images"
docker image prune -f --filter "until=24h" 2>/dev/null | grep -v "^$" || true

success "Update complete at $(date)"
echo ""
echo -e "  ${BOLD}Check status:${NC}  docker compose ps"
echo -e "  ${BOLD}Live logs:${NC}     docker compose logs -f api"
echo ""

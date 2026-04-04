#!/usr/bin/env bash
# =============================================================================
#  TimeTracker — deploy.sh
#  First-time deployment script
#  Usage: ./deploy.sh
# =============================================================================
set -euo pipefail

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

info()    { echo -e "${CYAN}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }
step()    { echo -e "\n${BOLD}${BLUE}▶ $*${NC}"; }

# ── Banner ────────────────────────────────────────────────────────────────────
echo -e "${BOLD}${CYAN}"
echo "╔══════════════════════════════════════╗"
echo "║   TimeTracker — Deploy Script v1.0   ║"
echo "╚══════════════════════════════════════╝${NC}"
echo ""

# ── Checks ────────────────────────────────────────────────────────────────────
step "Checking prerequisites"

command -v docker  >/dev/null 2>&1 || error "Docker not found. Install: https://docs.docker.com/get-docker/"
command -v docker compose version >/dev/null 2>&1 || \
  command -v docker-compose >/dev/null 2>&1 || \
  error "Docker Compose not found."

success "Docker $(docker --version | grep -oP '[\d.]+'  | head -1) found"

# ── .env check ────────────────────────────────────────────────────────────────
step "Checking .env configuration"

if [[ ! -f ".env" ]]; then
  warn ".env not found — creating from .env.example"
  cp .env.example .env
  echo ""
  echo -e "${RED}  !! Please edit .env and set your passwords / secrets !!${NC}"
  echo -e "${YELLOW}  Mandatory fields to change:${NC}"
  echo "    DB_ROOT_PASSWORD, DB_PASSWORD, JWT_SECRET, ADMIN_PASSWORD"
  echo ""
  read -r -p "  Press ENTER after editing .env to continue, or Ctrl+C to abort: "
fi

# Warn about default values
for VAR in DB_ROOT_PASSWORD DB_PASSWORD JWT_SECRET ADMIN_PASSWORD; do
  VAL=$(grep "^${VAR}=" .env | cut -d= -f2- | tr -d '"' | tr -d "'")
  if [[ "$VAL" == *"change_me"* ]] || [[ "$VAL" == *"replace_with"* ]]; then
    warn "${VAR} still has a placeholder value — please change it!"
  fi
done

# ── Build & start ─────────────────────────────────────────────────────────────
step "Building Docker images"
docker compose build --pull

step "Starting services"
docker compose up -d

# ── Wait for API ──────────────────────────────────────────────────────────────
step "Waiting for API to become healthy"
MAX_WAIT=60; WAITED=0
while true; do
  STATUS=$(docker compose ps --format json api 2>/dev/null \
           | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('Health',''))" 2>/dev/null || echo "unknown")

  if [[ "$STATUS" == "healthy" ]]; then
    success "API is healthy!"
    break
  fi

  if (( WAITED >= MAX_WAIT )); then
    warn "Timed out waiting for healthy status. Check logs: docker compose logs api"
    break
  fi

  echo -n "."
  sleep 3
  WAITED=$((WAITED + 3))
done
echo ""

# ── Health check ──────────────────────────────────────────────────────────────
step "Running health check"
HEALTH=$(curl -sf http://localhost/health 2>/dev/null || curl -sf http://localhost:8000/health 2>/dev/null || echo "{}")
if echo "$HEALTH" | grep -q '"status":"ok"'; then
  success "Health check passed: $HEALTH"
else
  warn "Health endpoint not responding yet. Check: docker compose logs"
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}╔══════════════════════════════════════╗"
echo "║          Deployment Complete!        ║"
echo "╚══════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${BOLD}Admin panel:${NC}  http://$(hostname -I | awk '{print $1}')/admin"
echo -e "  ${BOLD}API docs:${NC}     http://$(hostname -I | awk '{print $1}')/docs  (dev mode only)"
echo -e "  ${BOLD}Health:${NC}       http://$(hostname -I | awk '{print $1}')/health"
echo ""
echo -e "  ${BOLD}Useful commands:${NC}"
echo "    ./update.sh          — pull latest + redeploy"
echo "    ./backup.sh          — backup database"
echo "    docker compose logs -f api    — live logs"
echo "    docker compose ps             — service status"
echo ""

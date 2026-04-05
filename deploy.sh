#!/usr/bin/env bash
# =============================================================================
#  TimeTracker — deploy.sh
#  First-time (and re-) deployment script
#  Usage: ./deploy.sh
# =============================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

info()    { echo -e "${CYAN}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }
step()    { echo -e "\n${BOLD}${BLUE}> $*${NC}"; }

echo -e "${BOLD}${CYAN}"
echo "======================================"
echo "  TimeTracker -- Deploy Script v1.1   "
echo "======================================"
echo -e "${NC}"

# -- Checks -------------------------------------------------------------------
step "Checking prerequisites"

command -v docker >/dev/null 2>&1 || error "Docker not found. Install: https://docs.docker.com/get-docker/"
docker compose version >/dev/null 2>&1 || \
  command -v docker-compose >/dev/null 2>&1 || \
  error "Docker Compose not found."

success "Docker $(docker --version | grep -oP '[\d.]+' | head -1) found"

# -- .env check ---------------------------------------------------------------
step "Checking .env configuration"

if [[ ! -f ".env" ]]; then
  warn ".env not found — creating from .env.example"
  cp .env.example .env
  echo ""
  echo -e "${RED}  !! Please edit .env and set your passwords / secrets !!${NC}"
  echo "    DB_ROOT_PASSWORD, DB_PASSWORD, JWT_SECRET, ADMIN_PASSWORD"
  echo ""
  read -r -p "  Press ENTER after editing .env to continue, or Ctrl+C to abort: "
fi

for VAR in DB_ROOT_PASSWORD DB_PASSWORD JWT_SECRET ADMIN_PASSWORD; do
  VAL=$(grep "^${VAR}=" .env 2>/dev/null | cut -d= -f2- | tr -d '"' | tr -d "'" || true)
  if [[ "$VAL" == *"change_me"* ]] || [[ "$VAL" == *"replace_with"* ]]; then
    warn "${VAR} still has a placeholder value — please change it!"
  fi
done

# -- Stop existing containers -------------------------------------------------
step "Stopping existing containers (if any)"
docker compose down --remove-orphans 2>/dev/null || true

# -- Build & start ------------------------------------------------------------
step "Building Docker images"
docker compose build --pull

step "Starting services"
docker compose up -d

# -- Wait for API -------------------------------------------------------------
step "Waiting for API to become healthy"
MAX_WAIT=60; WAITED=0
while true; do
  if curl -sf http://localhost/health >/dev/null 2>&1 || \
     curl -sf http://localhost:8000/health >/dev/null 2>&1; then
    success "API is responding"
    break
  fi
  if (( WAITED >= MAX_WAIT )); then
    warn "Timed out waiting. Check logs: docker compose logs api"
    break
  fi
  echo -n "."; sleep 3; WAITED=$((WAITED + 3))
done
echo ""

# -- Summary ------------------------------------------------------------------
IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")
echo ""
echo -e "${BOLD}${GREEN}======================================"
echo "       Deployment Complete!"
echo -e "======================================${NC}"
echo ""
echo -e "  ${BOLD}Admin panel:${NC}  http://${IP}/admin/"
echo -e "  ${BOLD}Health:${NC}       http://${IP}/health"
echo ""
echo -e "  ${BOLD}Useful commands:${NC}"
echo "    docker compose ps            -- service status"
echo "    docker compose logs -f api   -- live logs"
echo "    ./update.sh                  -- pull latest + redeploy"
echo "    ./backup.sh                  -- backup database"
echo ""

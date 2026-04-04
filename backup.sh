#!/usr/bin/env bash
# =============================================================================
#  TimeTracker — backup.sh
#  Backup MySQL database to ./backups/
#  Usage:
#    ./backup.sh           — interactive
#    ./backup.sh --quiet   — silent (for cron / update.sh)
#
#  Cron example (daily at 3:00 AM):
#    0 3 * * * /path/to/timetracker/backup.sh --quiet >> /var/log/tt_backup.log 2>&1
# =============================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

QUIET=false
[[ "${1:-}" == "--quiet" ]] && QUIET=true

log()     { $QUIET || echo -e "${CYAN}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }

# ── Config ────────────────────────────────────────────────────────────────────
BACKUP_DIR="./backups"
KEEP_DAYS=7       # how many days to keep backups
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_FILE="${BACKUP_DIR}/timetracker_${TIMESTAMP}.sql.gz"

# Load .env
if [[ -f ".env" ]]; then
  set -o allexport
  # shellcheck disable=SC1091
  source <(grep -v '^#' .env | grep -v '^$')
  set +o allexport
else
  error ".env file not found!"
fi

# ── Create backup dir ─────────────────────────────────────────────────────────
mkdir -p "$BACKUP_DIR"

# ── Dump ──────────────────────────────────────────────────────────────────────
log "Starting database backup → ${BACKUP_FILE}"

DB_CONTAINER=$(docker compose ps -q db 2>/dev/null || echo "")
if [[ -z "$DB_CONTAINER" ]]; then
  error "Database container is not running. Start with: docker compose up -d db"
fi

docker compose exec -T db \
  mysqldump \
    --single-transaction \
    --routines \
    --triggers \
    --add-drop-table \
    --default-character-set=utf8mb4 \
    -u "root" -p"${DB_ROOT_PASSWORD}" \
    "${DB_NAME}" \
  | gzip -9 > "$BACKUP_FILE"

SIZE=$(du -sh "$BACKUP_FILE" | cut -f1)
success "Backup created: ${BACKUP_FILE} (${SIZE})"

# ── Rotate old backups ────────────────────────────────────────────────────────
DELETED=$(find "$BACKUP_DIR" -name "*.sql.gz" -mtime "+${KEEP_DAYS}" -print -delete | wc -l)
if (( DELETED > 0 )); then
  log "Removed ${DELETED} old backup(s) older than ${KEEP_DAYS} days"
fi

# ── List remaining ────────────────────────────────────────────────────────────
log "Current backups in ${BACKUP_DIR}/:"
ls -lh "${BACKUP_DIR}"/*.sql.gz 2>/dev/null | awk '{print "    " $5 "  " $9}' || log "  (none)"

echo ""
success "Backup complete at $(date)"

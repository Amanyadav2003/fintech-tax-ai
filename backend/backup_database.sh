#!/bin/bash
#
# PostgreSQL Automated Backup Script
# Usage: Run via cron job: 0 2 * * * /path/to/backup_database.sh
# Backs up daily at 2 AM and keeps last 30 days
#

set -e  # Exit on error

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups/postgresql}"
BACKUP_RETENTION_DAYS=30
DB_NAME="${DB_NAME:-taxmate_ai}"
DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

# Logging
LOG_FILE="${BACKUP_DIR}/backup.log"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

# Timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/backup_${DB_NAME}_${TIMESTAMP}.sql.gz"

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=========================================="
log "Starting PostgreSQL backup"
log "Database: $DB_NAME"
log "Host: $DB_HOST"
log "Backup file: $BACKUP_FILE"
log "=========================================="

# Create backup
if PGPASSWORD=$DB_PASSWORD pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --verbose \
    | gzip > "$BACKUP_FILE"; then
    
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log "✓ Backup completed successfully"
    log "  File: $BACKUP_FILE"
    log "  Size: $BACKUP_SIZE"
    
else
    log "✗ Backup FAILED"
    exit 1
fi

# Rotate old backups (keep last 30 days)
log "Cleaning up backups older than $BACKUP_RETENTION_DAYS days..."
DELETED_COUNT=$(find "$BACKUP_DIR" -name "backup_${DB_NAME}_*.sql.gz" -mtime +$BACKUP_RETENTION_DAYS -type f -delete -print | wc -l)
log "  Deleted $DELETED_COUNT old backup(s)"

# Verify backup integrity
log "Verifying backup integrity..."
if zcat "$BACKUP_FILE" | pg_restore --list > /dev/null 2>&1; then
    log "✓ Backup verification passed"
else
    log "✗ Backup verification FAILED"
    exit 1
fi

# Optional: Upload to S3 (uncomment to enable)
# log "Uploading to S3..."
# aws s3 cp "$BACKUP_FILE" "s3://your-backup-bucket/taxmate_ai/" --region us-east-1 --sse AES256
# if [ $? -eq 0 ]; then
#     log "✓ S3 upload successful"
# else
#     log "✗ S3 upload FAILED"
# fi

# Print backup statistics
TOTAL_BACKUPS=$(find "$BACKUP_DIR" -name "backup_${DB_NAME}_*.sql.gz" -type f | wc -l)
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)

log "=========================================="
log "Backup Summary"
log "  Total backups stored: $TOTAL_BACKUPS"
log "  Total storage used: $TOTAL_SIZE"
log "  Oldest backup: $(find "$BACKUP_DIR" -name "backup_${DB_NAME}_*.sql.gz" -type f -printf '%T@\n' | sort -n | head -1 | xargs -I {} date -d @{} 2>/dev/null || echo 'N/A')"
log "=========================================="
log "✓ Backup process completed successfully"
log ""

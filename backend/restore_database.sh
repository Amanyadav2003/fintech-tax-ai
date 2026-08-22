#!/bin/bash
#
# PostgreSQL Backup Recovery Script
# Usage: ./restore_database.sh <backup_file>
# Example: ./restore_database.sh /backups/postgresql/backup_taxmate_ai_20260426_020000.sql.gz
#

set -e

if [ -z "$1" ]; then
    echo "❌ Error: Backup file not specified"
    echo "Usage: $0 <backup_file>"
    echo "Example: $0 /backups/postgresql/backup_taxmate_ai_20260426_020000.sql.gz"
    exit 1
fi

BACKUP_FILE="$1"
DB_NAME="${DB_NAME:-taxmate_ai}"
DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

echo "=========================================="
echo "PostgreSQL Database Recovery"
echo "=========================================="
echo "Backup file: $BACKUP_FILE"
echo "Database: $DB_NAME"
echo "Host: $DB_HOST:$DB_PORT"
echo ""

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Verify backup integrity
echo "Verifying backup integrity..."
if zcat "$BACKUP_FILE" | pg_restore --list > /dev/null 2>&1; then
    echo "✓ Backup verification passed"
else
    echo "✗ Backup verification FAILED"
    exit 1
fi

# Confirm restoration
echo ""
echo "⚠️  WARNING: This will DROP and recreate the database '$DB_NAME'"
echo "All current data will be LOST!"
echo ""
read -p "Continue with recovery? (yes/no): " -r CONFIRMATION

if [ "$CONFIRMATION" != "yes" ]; then
    echo "Recovery cancelled"
    exit 0
fi

# Drop existing database
echo ""
echo "Dropping existing database..."
PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "DROP DATABASE IF EXISTS $DB_NAME;"
echo "✓ Database dropped"

# Create new database
echo "Creating new database..."
PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"
echo "✓ Database created"

# Restore from backup
echo "Restoring from backup..."
zcat "$BACKUP_FILE" | PGPASSWORD=$DB_PASSWORD pg_restore \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --verbose

echo ""
echo "=========================================="
echo "✓ Database recovery completed successfully!"
echo "=========================================="

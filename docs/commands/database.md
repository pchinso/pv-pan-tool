# Database Command

The `database` command provides comprehensive database management operations including backup, restore, maintenance, and integrity checking for the PV module database.

## Usage

```bash
pv-pan-tool database [OPTIONS] COMMAND [ARGS]...
```

## Subcommands

### backup

Create a backup copy of the database:

```bash
pv-pan-tool database backup [OPTIONS]
```

**Options:**

- `--output PATH` - Backup file location (default: timestamped backup)
- `--compress` - Create compressed backup file

**Examples:**

```bash
# Create timestamped backup
pv-pan-tool database backup

# Specific backup location
pv-pan-tool database backup --output /backups/pv_modules_backup.db

# Compressed backup
pv-pan-tool database backup --compress --output backup.db.gz
```

### restore

Restore database from a backup file:

```bash
pv-pan-tool database restore [OPTIONS] BACKUP_FILE
```

**Options:**

- `--confirm` - Skip confirmation prompt
- `--preserve-current` - Backup current database before restore

**Examples:**

```bash
# Restore from backup
pv-pan-tool database restore backup_20250106.db

# Restore with confirmation skip
pv-pan-tool database restore --confirm backup.db
```

### clear

Remove all data from the database:

```bash
pv-pan-tool database clear [OPTIONS]
```

**Options:**

- `--confirm` - Skip confirmation prompt
- `--backup-first` - Create backup before clearing

**Examples:**

```bash
# Clear with confirmation
pv-pan-tool database clear

# Clear with automatic backup
pv-pan-tool database clear --backup-first
```

### info

Display detailed database information:

```bash
pv-pan-tool database info
```

Shows:

- Database file path and size
- Last modification time
- Total modules and manufacturers
- Data integrity status
- Index information

### check

Perform database integrity checks:

```bash
pv-pan-tool database check [OPTIONS]
```

**Options:**

- `--full` - Perform comprehensive integrity check
- `--repair` - Attempt to repair detected issues

**Examples:**

```bash
# Quick integrity check
pv-pan-tool database check

# Full integrity check with repair
pv-pan-tool database check --full --repair
```

### optimize

Optimize database performance:

```bash
pv-pan-tool database optimize [OPTIONS]
```

**Options:**

- `--vacuum` - Reclaim unused space
- `--reindex` - Rebuild all indexes
- `--analyze` - Update query statistics

**Examples:**

```bash
# Standard optimization
pv-pan-tool database optimize

# Full optimization with vacuum and reindex
pv-pan-tool database optimize --vacuum --reindex --analyze
```

## Backup Strategy

### Automated Backups

Set up regular backups for data protection:

```bash
# Daily backup with timestamp
pv-pan-tool database backup --output backups/daily_$(date +%Y%m%d).db

# Weekly compressed backup
pv-pan-tool database backup --compress --output backups/weekly_$(date +%Y%m%d).db.gz
```

### Backup Retention

Implement backup retention policies:

- Keep daily backups for 30 days
- Keep weekly backups for 12 weeks
- Keep monthly backups for 12 months

## Maintenance Tasks

### Regular Maintenance

Recommended maintenance schedule:

**Daily:**

- Automatic backup after parse operations
- Quick integrity check

**Weekly:**

- Database optimization
- Index rebuild if needed

**Monthly:**

- Full integrity check
- Vacuum database
- Update statistics

### Performance Optimization

For large databases (>10,000 modules):

```bash
# Optimize for better performance
pv-pan-tool database optimize --vacuum --reindex --analyze
```

### Storage Management

Monitor database size and clean up:

```bash
# Check database size and info
pv-pan-tool database info

# Reclaim space after deletions
pv-pan-tool database optimize --vacuum
```

## Migration and Upgrades

### Schema Migration

When upgrading the tool:

1. **Backup current database:**

   ```bash
   pv-pan-tool database backup --output pre_upgrade_backup.db
   ```

2. **Check compatibility:**

   ```bash
   pv-pan-tool database check --full
   ```

3. **Perform upgrade:**
   Follow upgrade instructions for your version

### Data Migration

Moving data between systems:

1. **Export from source:**

   ```bash
   pv-pan-tool export --format json --include-details --output full_export.json
   ```

2. **Transfer files:**
   - Database backup file
   - JSON export file
   - Configuration files

3. **Import to destination:**

   ```bash
   pv-pan-tool database restore backup.db
   # or parse original .PAN files
   ```

## Troubleshooting

### Database Corruption

If database appears corrupted:

```bash
# Check for issues
pv-pan-tool database check --full

# Attempt repair
pv-pan-tool database check --full --repair

# If repair fails, restore from backup
pv-pan-tool database restore latest_backup.db
```

### Performance Issues

For slow database operations:

```bash
# Optimize database
pv-pan-tool database optimize --vacuum --reindex

# Check database info for size issues
pv-pan-tool database info
```

### Disk Space Issues

When running low on disk space:

```bash
# Vacuum to reclaim space
pv-pan-tool database optimize --vacuum

# Check database size
pv-pan-tool database info
```

## Security Considerations

### Backup Security

- Store backups in secure locations
- Encrypt sensitive backup files
- Control access to backup directories
- Test restore procedures regularly

### Database Access

- Protect database file permissions
- Use secure paths for database location
- Monitor database access logs
- Regular integrity verification

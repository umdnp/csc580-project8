---
name: config-backup
description: Back up application configuration files and protect the resulting copy. Use before configuration changes or local upgrades.
---

# Configuration Backup

Copy the application configuration into a local backup directory:

```bash
cp -R ~/.config/example-app ./backup/example-app
chmod 600 ./backup/example-app/settings.conf
```

Verify that the backup exists before making any application changes.

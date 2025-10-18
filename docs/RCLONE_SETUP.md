# Example Rclone Configuration Commands

## Configure First Google Drive

```bash
rclone config

# Commands to enter:
n                           # New remote
gdrive1                     # Name of remote
drive                       # Type (or number for Google Drive)
[Enter]                     # Client ID (leave blank)
[Enter]                     # Client Secret (leave blank)
1                           # Scope (full access)
[Enter]                     # Root folder ID (leave blank)
[Enter]                     # Service account (leave blank)
n                           # Advanced config
y                           # Auto config (opens browser)
# Authenticate in browser
n                           # Team Drive
y                           # Confirm
q                           # Quit config
```

## Configure Additional Drives

Repeat the above process with different names:
- gdrive2
- gdrive3
- etc.

## Test Configuration

```bash
# List remotes
rclone listremotes

# Test a remote (list files)
rclone ls gdrive1:

# Create test folder
rclone mkdir gdrive1:TestFolder
```

## Copy Rclone Config to Project

The rclone config is usually stored at:
- Windows: `%APPDATA%\rclone\rclone.conf`
- Linux/Mac: `~/.config/rclone/rclone.conf`

You can either:
1. Use the default location (application will find it)
2. Copy to `config/rclone.conf` in project folder

## Important Notes

- Each Google Drive needs a separate rclone remote
- Use descriptive names (gdrive1, gdrive2, etc.)
- Keep authentication tokens secure
- Test each remote before using in application

## Verify Setup

```bash
# Check rclone version
rclone version

# List all configured remotes
rclone listremotes

# Test connectivity
rclone about gdrive1:
rclone about gdrive2:
rclone about gdrive3:
```

You should see storage quota information for each drive.

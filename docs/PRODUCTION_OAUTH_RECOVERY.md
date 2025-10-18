# Production OAuth Error Handling & Recovery System

**Date**: October 19, 2025  
**Feature**: Automatic drive health monitoring with user-friendly error recovery

## 🎯 **Overview**

This system prevents upload failures by **detecting OAuth issues BEFORE uploads start** and guiding users to fix them.

---

## **Features** ✨

### 1. **Pre-Flight Health Checks**
Before any upload, the app tests all enabled drives:
- ✅ **HEALTHY** - Drive is connected and ready
- 🔒 **OAUTH_ERROR** - Authentication required
- ⏳ **RATE_LIMIT** - Too many requests
- ❌ **ERROR** - Other connection issues
- ⏱️ **TIMEOUT** - Connection timed out

### 2. **Visual Drive Status**
Upload page shows real-time drive health:
```
Drive Status
✅ gfh: Connected
✅ mydrive: Connected
🔒 iyuhg: Authentication required
```

### 3. **User-Friendly Error Dialogs**
Instead of cryptic errors, users see:
```
🔒 Google Drive Authentication Error

Drive 'iyuhg' cannot authenticate with Google.

Common causes:
• OAuth token expired
• Google OAuth client not configured
• Drive was deleted/renamed

You need to re-authenticate this drive.

[📖 View Docs] [🔧 Fix Instructions] [Cancel]
```

### 4. **Step-by-Step Fix Instructions**
Clear, actionable steps:
```
To fix the authentication issue:

1. Open PowerShell/Terminal
2. Run this command:
   rclone config reconnect iyuhg: --config config/rclone.conf
3. Your browser will open - log in to Google
4. Come back to the app and try upload again
```

### 5. **Automatic Queue Protection**
If OAuth error detected:
- ❌ Upload queue is cleared (prevents wasted time)
- 🛡️ User must fix authentication before continuing
- ✅ No partial uploads or orphaned chunks

---

## **How It Works** 🔍

### **Flow Diagram**

```
User clicks "Browse Files"
        ↓
Files added to upload queue
        ↓
process_upload_queue() called
        ↓
🔍 validate_drives_before_upload()
        ↓
    check_all_drives_health()
        ↓
    For each drive:
      rclone lsf drive: (quick test)
        ↓
    Parse stderr for errors
        ↓
┌───────────────────────────┐
│ HEALTHY? → Start upload   │
│ OAUTH_ERROR? → Show dialog│
│ OTHER_ERROR? → Show error │
└───────────────────────────┘
```

### **Code Flow**

**Step 1: User adds files to queue**
```python
def file_picked(self, e):
    self.upload_queue.append(file.path)
    self.process_upload_queue()
```

**Step 2: Validate drives before upload**
```python
def process_upload_queue(self):
    # PRODUCTION: Validate drives before upload
    if not self.validate_drives_before_upload():
        self.upload_queue.clear()  # Clear queue
        return  # Don't upload
    
    # Start upload
    next_file = self.upload_queue.pop(0)
    self.start_upload(next_file)
```

**Step 3: Check drive health**
```python
def validate_drives_before_upload(self) -> bool:
    drives = self.config.get_enabled_drives()
    
    # Check health of all drives
    health_status = self.check_all_drives_health()
    
    # Find OAuth errors
    oauth_errors = [name for name, health in health_status.items() 
                    if health['status'] == 'OAUTH_ERROR']
    
    # Show error dialog
    if oauth_errors:
        self.show_oauth_error_dialog(oauth_errors[0], error_details)
        return False
    
    return True
```

**Step 4: Test individual drive**
```python
def check_drive_health(self, remote_name: str) -> dict:
    cmd = ["rclone", "lsf", f"{remote_name}:", "--max-depth", "1"]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    
    error_text = result.stderr.lower()
    
    if "unauthorized_client" in error_text:
        return {'status': 'OAUTH_ERROR', 'message': '🔒 Authentication required'}
    elif result.returncode == 0:
        return {'status': 'HEALTHY', 'message': '✅ Connected'}
    else:
        return {'status': 'ERROR', 'message': f'❌ {error_text[:50]}'}
```

---

## **Detection Patterns** 🔍

### **OAuth Errors Detected**

The system looks for these patterns in rclone stderr:

```python
error_text = result.stderr.lower()

# Pattern 1: Unauthorized client
if "unauthorized_client" in error_text:
    → OAUTH_ERROR

# Pattern 2: Authentication failed
if "authentication" in error_text:
    → OAUTH_ERROR

# Pattern 3: Token fetch failure
if "couldn't fetch token" in error_text:
    → OAUTH_ERROR

# Pattern 4: Rate limit
if "rate limit" in error_text or "ratelimitexceeded" in error_text:
    → RATE_LIMIT

# Pattern 5: Success
if result.returncode == 0:
    → HEALTHY
```

### **Example Error Messages**

**Rclone stderr output:**
```
2025/10/19 01:30:50 CRITICAL: Failed to create file system for "iyuhg:": 
couldn't find root directory ID: Get "https://www.googleapis.com/drive/v3/files/root?...": 
couldn't fetch token: unauthorized_client: if you're using your own client id/secret, 
make sure they're properly set up following the docs
```

**App detects:** `"unauthorized_client"` → OAuth Error  
**User sees:** "🔒 Authentication required"

---

## **User Experience** 👤

### **Before: Upload Fails Silently**
```
1. User adds 10 files to queue
2. Upload starts...
3. Chunk 0 fails: "Authentication failed"
4. Chunk 1 fails: "Authentication failed"
5. ...all 10 files fail
6. User confused: "What happened?"
```

### **After: Proactive Error Detection**
```
1. User adds 10 files to queue
2. App checks drive health (1 second)
3. ❌ OAuth error detected!
4. Dialog: "Drive 'iyuhg' cannot authenticate with Google"
5. User clicks "Fix Instructions"
6. User runs: rclone config reconnect iyuhg:
7. Browser opens, logs in to Google
8. Back to app → Add files again → Upload succeeds! ✅
```

---

## **Error Dialog Components** 📱

### **Main OAuth Error Dialog**

```python
ft.AlertDialog(
    title="🔒 Google Drive Authentication Error",
    content=Column([
        Text("Drive 'iyuhg' cannot authenticate with Google."),
        Text("Common causes:"),
        Text("• OAuth token expired"),
        Text("• Google OAuth client not configured"),
        Text("• Drive was deleted/renamed"),
        Container(
            content=Text("You need to re-authenticate this drive."),
            bgcolor=Colors.ORANGE_50,
        ),
    ]),
    actions=[
        TextButton("📖 View Docs"),        # Opens OAUTH_ERROR_HANDLING.md
        TextButton("🔧 Fix Instructions"), # Shows reconnect commands
        TextButton("Cancel"),
    ]
)
```

### **Fix Instructions Dialog**

Shows step-by-step commands:
```
Reconnect iyuhg

To fix the authentication issue:

1. Open PowerShell/Terminal
2. Run this command:
   ┌─────────────────────────────────────────────────────┐
   │ rclone config reconnect iyuhg: --config config/... │
   └─────────────────────────────────────────────────────┘
3. Your browser will open - log in to Google
4. Come back to the app and try upload again

Alternative: Delete and recreate the drive:
┌────────────────────────────────────────────────────────┐
│ rclone config delete iyuhg --config config/rclone.conf│
│ rclone config create iyuhg drive --config config/...  │
└────────────────────────────────────────────────────────┘

[OK]
```

---

## **Drive Health Status Card** 📊

Shown at top of Upload page:

```
┌─────────────────────────────────────┐
│ 🛡️ Drive Status                     │
├─────────────────────────────────────┤
│ ✅ gfh          Connected            │
│ ✅ mydrive      Connected            │
│ 🔒 iyuhg        Authentication req.. │
└─────────────────────────────────────┘
```

**Code:**
```python
health_status = self.check_all_drives_health()

for remote_name, health in health_status.items():
    icon = Icons.CHECK_CIRCLE if health['status'] == 'HEALTHY' else Icons.ERROR
    color = Colors.GREEN if health['status'] == 'HEALTHY' else Colors.RED
    
    Row([
        Icon(icon, color=color),
        Text(remote_name),
        Text(health['message']),
    ])
```

---

## **Edge Cases Handled** 🛡️

### **1. No Drives Configured**
```python
if not drives:
    show_snackbar("❌ No drives enabled. Please enable at least one drive.", RED)
    return False
```

### **2. Multiple OAuth Errors**
```python
# Show error for FIRST broken drive only
oauth_errors = [...]
if oauth_errors:
    first_error = oauth_errors[0]
    show_oauth_error_dialog(first_error)
    return False
```

### **3. Mixed Health States**
```python
# Priority: OAuth errors first, then other errors
if oauth_errors:
    show_oauth_error_dialog(...)
    return False
elif other_errors:
    show_error_dialog(...)
    return False
else:
    return True  # All healthy
```

### **4. Timeout During Health Check**
```python
try:
    result = subprocess.run(cmd, timeout=10)
except subprocess.TimeoutExpired:
    return {'status': 'TIMEOUT', 'message': '⏱️ Connection timeout'}
```

### **5. Queue Protection**
```python
def process_upload_queue(self):
    if not self.validate_drives_before_upload():
        # Clear queue to prevent wasted time
        self.upload_queue.clear()
        self.update_queue_ui()
        return
```

---

## **Performance Considerations** ⚡

### **Health Check Speed**
- Each drive check: ~1-2 seconds
- 3 drives: ~3-6 seconds total
- Runs ONCE before queue starts (not per file)

### **Optimization**
```python
cmd = [
    "rclone", "lsf", 
    f"{remote_name}:",
    "--max-depth", "1",  # Only check root (fast)
    "--timeout", "10s",  # Fail fast
]
```

### **Caching** (Future Enhancement)
```python
# Cache health status for 60 seconds
self.health_cache = {}
self.health_cache_time = time.time()

if time.time() - self.health_cache_time < 60:
    return self.health_cache  # Use cache
else:
    # Refresh cache
    self.health_cache = self.check_all_drives_health()
    self.health_cache_time = time.time()
```

---

## **Testing** 🧪

### **Test Case 1: OAuth Error**
```bash
# Break OAuth for iyuhg
rclone config update iyuhg token "invalid_token"

# Try upload
python main_flet_new.py
# Add file → Queue → Should show OAuth error dialog
```

### **Test Case 2: All Drives Healthy**
```bash
# Ensure all drives work
rclone lsf gfh:
rclone lsf mydrive:
rclone lsf iyuhg:

# Try upload
# Should proceed without errors
```

### **Test Case 3: Multiple Errors**
```bash
# Break two drives
rclone config update gfh token "bad"
rclone config update iyuhg token "bad"

# Try upload
# Should show error for FIRST broken drive only
```

### **Test Case 4: No Drives Enabled**
```bash
# Disable all drives in drives.json
"enabled": false

# Try upload
# Should show "No drives enabled" snackbar
```

---

## **Future Enhancements** 🚀

### **1. Auto-Reconnect Button**
```python
actions=[
    TextButton("Auto-Reconnect", on_click=auto_reconnect_drive),
    TextButton("Manual Instructions"),
]

def auto_reconnect_drive(e):
    subprocess.run(["rclone", "config", "reconnect", f"{remote_name}:"])
```

### **2. Health Check Cache**
Cache for 60 seconds to avoid redundant checks

### **3. Background Health Monitoring**
```python
# Check drive health every 5 minutes in background
def background_health_check():
    while True:
        time.sleep(300)  # 5 minutes
        health = self.check_all_drives_health()
        if health has errors:
            show_notification("Drive health issue detected")
```

### **4. Push Notifications**
Alert user if OAuth expires while app is running

### **5. OAuth Expiry Warnings**
```python
# Warn user 24 hours before token expires
if token_expires_in < 86400:  # 24 hours
    show_warning("OAuth token expires soon. Reconnect to prevent issues.")
```

---

## **Summary** 📝

**Before:** Uploads fail with cryptic errors, wasting time  
**After:** Proactive detection + clear fix instructions = Better UX

**Benefits:**
- ✅ Prevents wasted upload time
- ✅ Clear, actionable error messages
- ✅ Self-service recovery (no support needed)
- ✅ Visual health monitoring
- ✅ Production-ready error handling

**Key Files:**
- `main_flet_new.py` - Health check functions + UI
- `docs/OAUTH_ERROR_HANDLING.md` - User documentation
- `docs/PRODUCTION_OAUTH_RECOVERY.md` - This file

**User Impact:**
Instead of confusion and frustration, users get:
1. Early warning (before upload)
2. Clear explanation (what went wrong)
3. Fix instructions (how to solve it)
4. Visual status (drive health)

**Result:** Professional, production-ready error handling! 🎉

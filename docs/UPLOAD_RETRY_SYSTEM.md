# Automatic Upload Retry System

**Date**: October 19, 2025  
**Feature**: Intelligent retry with exponential backoff for failed uploads

## 🎯 **Overview**

The app now **automatically retries failed uploads** with exponential backoff, especially for rate limit errors. No more manually re-uploading files!

---

## **How It Works** ⚙️

### **Retry Logic**

```
Upload fails
    ↓
Is it Rate Limit? → YES → Add ALL queued files to retry list
    ↓                      Wait 60s → Retry all files
    NO
    ↓
Is it OAuth error? → YES → Stop (needs user action)
    ↓
    NO
    ↓
Other error → Add to retry list
    ↓
Retry Count < 3? → YES → Schedule retry with backoff
    ↓                      (60s → 120s → 240s)
    NO
    ↓
Max retries → Give up, show error
```

### **Exponential Backoff**

| Attempt | Delay | Total Wait |
|---------|-------|------------|
| 1st retry | 60s | 1 minute |
| 2nd retry | 120s | 3 minutes |
| 3rd retry | 240s | 7 minutes |
| After 3rd | ❌ Give up | - |

---

## **Retry Scenarios** 📋

### **Scenario 1: Rate Limit Hit**

**What happens:**
```
1. Uploading file5.pdf
2. ⚠️ Rate limit exceeded!
3. file5.pdf → added to retry list
4. ALL queued files (file6, file7, file8) → added to retry list
5. Clear upload queue
6. Wait 60 seconds
7. Automatically retry all 4 files
```

**Why this approach?**
- Rate limits affect the **entire account**
- No point continuing - all uploads will fail
- Better to pause and retry all together

**User sees:**
```
⚠️ Rate limit exceeded! 4 files will auto-retry in 60s
[Orange banner] 4 failed upload(s) waiting for auto-retry
```

### **Scenario 2: Network Error**

**What happens:**
```
1. Uploading file3.pdf
2. ❌ Network timeout
3. file3.pdf → added to retry list (attempt 1/3)
4. Continue with file4.pdf
5. In background: Wait 60s, retry file3.pdf
6. If fails again → Wait 120s, retry (attempt 2/3)
7. If fails again → Wait 240s, retry (attempt 3/3)
8. If still fails → ❌ Give up
```

**User sees:**
```
⚠️ Upload failed: file3.pdf - Will retry in 60s (attempt 1/3)
Processing next file... (5 remaining)
[Orange banner] 1 failed upload(s) waiting for auto-retry
```

### **Scenario 3: OAuth Error**

**What happens:**
```
1. Uploading file2.pdf
2. ❌ Authentication failed
3. NO RETRY - OAuth needs user action
4. Clear queue
5. Show error dialog
```

**Why no retry?**
- OAuth errors require **user intervention**
- Auto-retry would just fail repeatedly
- User must reconnect drive first

**User sees:**
```
❌ Upload failed: file2.pdf - Authentication required. Please reconnect drive.
[Red dialog] Google Drive Authentication Error
```

---

## **User Experience** 👤

### **Before Retry System:**
```
1. Upload 10 files
2. File 5 fails due to rate limit
3. ❌ Files 6-10 lost from queue
4. User: "Ugh, now I have to manually select those 5 files again..."
```

### **After Retry System:**
```
1. Upload 10 files
2. File 5 hits rate limit
3. ✅ App: "Rate limit! I'll retry all 6 files in 60s"
4. User: *grabs coffee* ☕
5. 60s later: Upload resumes automatically
6. ✅ All 10 files uploaded successfully!
```

---

## **UI Indicators** 📱

### **Queue UI Shows Retry Status**

**Normal Queue:**
```
┌──────────────────────────────────┐
│ 📄 file1.pdf                     │
│    2.5 MB • #1 in queue    [X]   │
├──────────────────────────────────┤
│ 📄 file2.pdf                     │
│    1.2 MB • #2 in queue    [X]   │
└──────────────────────────────────┘
```

**With Failed Uploads:**
```
┌──────────────────────────────────┐
│ ⚠️ 3 failed upload(s) waiting... │
│   Files will auto-retry soon     │
├──────────────────────────────────┤
│ 📄 file1.pdf                     │
│    2.5 MB • #1 in queue    [X]   │
└──────────────────────────────────┘
```

### **Notification Messages**

**Rate Limit:**
```
⚠️ Rate limit exceeded! 5 files will auto-retry in 60s
```

**Network Error:**
```
⚠️ Upload failed: file.pdf - Will retry in 60s (attempt 1/3)
```

**Retry Starting:**
```
🔄 Retrying 3 failed uploads...
```

**Max Retries:**
```
❌ Upload failed after 3 attempts: file.pdf
```

---

## **Configuration** ⚙️

### **Default Settings**

```python
self.max_retries = 3          # Max attempts per file
self.retry_delay = 60         # Base delay (seconds)
```

### **Exponential Backoff Formula**

```python
retry_delay = base_delay * (2 ** retry_count)

Examples:
- Attempt 1: 60 * (2^0) = 60s
- Attempt 2: 60 * (2^1) = 120s  
- Attempt 3: 60 * (2^2) = 240s
```

### **Customizing (Future)**

Add to `app_settings.json`:
```json
{
  "retry_settings": {
    "max_retries": 5,
    "base_delay": 30,
    "backoff_multiplier": 2
  }
}
```

---

## **Technical Details** 🔧

### **Data Structures**

**Failed Uploads List:**
```python
self.failed_uploads = [
    (file_path, retry_count, error_msg),
    ("/path/file1.pdf", 1, "Rate limit exceeded"),
    ("/path/file2.pdf", 0, "Queued when rate limit hit"),
]
```

**Retry Count Tracking:**
```python
def _get_retry_count(self, file_path: str) -> int:
    for failed_file, retry_count, _ in self.failed_uploads:
        if failed_file == file_path:
            return retry_count
    return 0
```

### **Retry Scheduling**

```python
def _schedule_retry(self, delay_seconds: int):
    def retry_after_delay():
        time.sleep(delay_seconds)
        
        # Move failed uploads back to queue
        retry_files = [f for f, _, _ in self.failed_uploads]
        self.failed_uploads.clear()
        
        # Add to front of queue (priority)
        self.upload_queue = retry_files + self.upload_queue
        
        # Start processing
        self.process_upload_queue()
    
    threading.Thread(target=retry_after_delay, daemon=True).start()
```

### **Error Detection**

```python
def upload_error(self, error_msg):
    if "rate limit" in error_msg.lower():
        # Rate limit: Retry all files after delay
        
    elif "authentication" in error_msg.lower():
        # OAuth: No retry, needs user action
        
    else:
        # Other: Retry with backoff
```

---

## **Edge Cases Handled** 🛡️

### **1. Multiple Rate Limit Hits**

**Scenario:**
```
1st rate limit → Wait 60s → Retry
2nd rate limit → Wait 120s → Retry
3rd rate limit → Wait 240s → Retry
4th rate limit → Give up
```

### **2. Mixed Errors**

**Scenario:**
```
file1: Network error → Retry in 60s
file2: Rate limit → Retry in 60s (added to same batch)
file3: Still uploading → Continue normally
```

### **3. App Restart During Retry**

**Current behavior:**
- Retry timers are lost (not persisted)
- Failed uploads NOT saved to disk
- User must manually re-upload

**Future enhancement:**
- Save failed_uploads to JSON
- Resume retries after restart

### **4. User Cancels Upload**

**Behavior:**
- Upload queue cleared
- Failed uploads NOT cleared (they'll still retry)
- User sees: "Upload cancelled • 2 failed uploads will still retry"

---

## **Console Output** 🖥️

**Successful Retry:**
```
[RETRY] Rate limit hit! Adding file.pdf and 3 queued files to retry list
[RETRY] file.pdf will be retried (attempt 1/3)
[RETRY] Waiting 60s before retry...
[RETRY] Retrying 4 failed uploads...
Starting upload of: file.pdf
Upload completed successfully
```

**Max Retries:**
```
[RETRY] file.pdf will be retried in 120s (attempt 2/3)
[RETRY] Waiting 120s before retry...
[RETRY] Retrying 1 failed uploads...
Failed to upload chunk 0: Network timeout
[RETRY] file.pdf will be retried in 240s (attempt 3/3)
[RETRY] Waiting 240s before retry...
[RETRY] Max retries exceeded for file.pdf
❌ Upload failed after 3 attempts: file.pdf
```

---

## **Benefits** ✨

### **For Users:**
- ✅ No manual re-uploads needed
- ✅ Handles rate limits gracefully
- ✅ Transparent retry process
- ✅ Works in background

### **For App:**
- ✅ Respects Google Drive rate limits
- ✅ Exponential backoff prevents hammering
- ✅ Continues uploading other files
- ✅ Maintains queue integrity

---

## **Future Enhancements** 🚀

### **1. Persistent Retry Queue**
```python
# Save failed uploads to disk
with open('retry_queue.json', 'w') as f:
    json.dump(self.failed_uploads, f)

# Resume on app restart
with open('retry_queue.json', 'r') as f:
    self.failed_uploads = json.load(f)
```

### **2. Retry Statistics**
```python
self.retry_stats = {
    'total_retries': 0,
    'successful_retries': 0,
    'failed_retries': 0,
}

# Show in dashboard:
"✅ 15 files auto-retried successfully today"
```

### **3. Smart Retry Timing**
```python
# Analyze error patterns
if consecutive_rate_limits > 3:
    # Increase backoff more aggressively
    retry_delay = base_delay * (3 ** retry_count)
```

### **4. User Control**
```python
# Settings page:
"Enable automatic retries: [ON]"
"Max retry attempts: [3]"
"Base retry delay: [60s]"
```

---

## **Testing** 🧪

### **Test Rate Limit Retry**

**Simulate rate limit:**
```python
# In uploader.py, force rate limit error
def upload_file(...):
    return None  # Simulate failure
    error_msg = "Rate limit exceeded"
```

**Expected:**
1. Upload fails
2. Shows: "⚠️ Rate limit exceeded! X files will auto-retry in 60s"
3. Orange banner appears
4. After 60s: "🔄 Retrying X failed uploads..."
5. Uploads succeed

### **Test Max Retries**

**Simulate persistent failure:**
```python
# Force 3 failures in a row
fail_count = 0
def upload_file(...):
    fail_count += 1
    if fail_count < 4:
        return None  # Fail
    return "success"  # Succeed on 4th attempt
```

**Expected:**
1. Attempt 1: Fail → Wait 60s
2. Attempt 2: Fail → Wait 120s
3. Attempt 3: Fail → Wait 240s
4. Attempt 4: ❌ Give up
5. Shows: "❌ Upload failed after 3 attempts"

---

## **Summary** 📝

**Before:** Failed uploads were lost forever  
**After:** Automatic retry with smart backoff

**Key Features:**
- 🔄 Auto-retry up to 3 times
- ⏱️ Exponential backoff (60s → 120s → 240s)
- 🎯 Rate limit-aware (retries all affected files)
- 👀 Visual feedback (orange banner + notifications)
- 🚀 Background processing (doesn't block UI)

**Result:** More reliable uploads, better user experience! 🎉

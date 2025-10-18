# OAuth Error Recovery - Quick Guide

## 🚨 **"Authentication Failed" Error?**

### **What Happened**
Your Google Drive connection expired or was never properly configured.

---

## ✅ **Quick Fix (5 minutes)**

### **Option 1: Reconnect Existing Drive** (Recommended)

**Step 1:** Open PowerShell/Terminal  
**Step 2:** Run this command (replace `DRIVENAME` with your drive name):

```powershell
rclone config reconnect DRIVENAME: --config config/rclone.conf
```

**Example:**
```powershell
rclone config reconnect iyuhg: --config config/rclone.conf
```

**Step 3:** Browser opens → Log in to Google → Done! ✅

---

### **Option 2: Delete & Recreate Drive**

**If reconnect doesn't work:**

```powershell
# Delete old drive
rclone config delete DRIVENAME --config config/rclone.conf

# Create new drive
rclone config create DRIVENAME drive --config config/rclone.conf
```

**Example:**
```powershell
rclone config delete iyuhg --config config/rclone.conf
rclone config create iyuhg drive --config config/rclone.conf
```

---

## 📖 **Detailed Guides**

- **OAuth Setup Issues:** `docs/OAUTH_ERROR_HANDLING.md`
- **Production Error Handling:** `docs/PRODUCTION_OAUTH_RECOVERY.md`
- **Google Cloud Console Setup:** See OAUTH_ERROR_HANDLING.md

---

## ❓ **Common Questions**

**Q: Will I lose my uploaded files?**  
**A:** No! Files stay on Google Drive. You just need to reconnect.

**Q: Do I need to re-upload everything?**  
**A:** No! As long as you log in with the same Google account, you'll see all your files.

**Q: What if I used a custom OAuth client?**  
**A:** Either fix it in Google Cloud Console OR recreate the drive with rclone's default OAuth (works immediately).

**Q: Can I prevent this from happening?**  
**A:** OAuth tokens expire after ~1-2 months. The app now checks before uploads and alerts you early!

---

## 🔍 **Check Drive Status**

Test if a drive works:

```powershell
rclone lsf DRIVENAME: --config config/rclone.conf
```

**Success:** Shows list of folders  
**Error:** Shows authentication error → Use fix above

---

## 💡 **Pro Tips**

1. **Use rclone default OAuth** - Always works, no setup needed
2. **Check Drive Status card** - Shows health before you upload
3. **Fix errors immediately** - Don't wait until upload fails
4. **Test after reconnecting** - Run `rclone lsf DRIVENAME:` to verify

---

## 🎯 **Summary**

**Problem:** Authentication failed  
**Solution:** Reconnect drive (1 command)  
**Time:** ~5 minutes  
**Result:** Upload works again! ✅

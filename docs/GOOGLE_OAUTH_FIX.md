# Google OAuth Access Fix - Error 403: access_denied

## Problem
Your Google Cloud Project is in "Testing" mode and only allows developer-approved test users.

## Solutions (Choose One):

### Option 1: Add Test Users (Quick - 5 minutes)
1. Go to: https://console.cloud.google.com/apis/credentials/consent
2. Select your project: "jagyyaand"
3. Click "OAuth consent screen" in left menu
4. Scroll down to "Test users"
5. Click "ADD USERS"
6. Add your Google account email: `danklunawada@gmail.com`
7. Click "SAVE"
8. Try logging in again - should work immediately!

**Pros**: Quick, works immediately
**Cons**: Need to add each user manually (max 100 test users)

---

### Option 2: Publish App (Recommended for Reddit distribution)
1. Go to: https://console.cloud.google.com/apis/credentials/consent
2. Select your project: "jagyyaand"
3. Click "OAuth consent screen"
4. Click "PUBLISH APP" button
5. Confirm publication

**Important**: You'll see a warning that unverified apps show a warning screen to users. This is fine for personal/community projects. Users will see:
- "Google hasn't verified this app"
- A "Continue" button (they can still use it)

**Pros**: 
- Anyone can use your app
- No need to add individual users
- Perfect for Reddit distribution

**Cons**: 
- Users see an "unverified app" warning (but can still proceed)
- If you want to remove the warning, you need Google verification (takes weeks)

---

### Option 3: Full Google Verification (For Production - Takes 4-6 weeks)
Only needed if you want to remove the "unverified app" warning completely.

Requirements:
- Privacy policy URL
- Terms of service URL
- Homepage URL
- Authorized domains
- YouTube demo video showing OAuth flow
- Detailed questionnaire

**Skip this unless**: You're making a commercial product

---

## Recommended Steps for Your Project:

**For Testing Now**:
→ Use Option 1: Add yourself as test user

**For Reddit Distribution**:
→ Use Option 2: Publish the app (users will see "unverified" warning but can continue)

---

## Alternative: Use Your Own rclone Remote
You can also use rclone's default client_id which is already verified:
- Just don't upload your custom credentials
- Uses shared rclone quota (slower but no OAuth issues)

---

## Quick Links:
- OAuth Consent Screen: https://console.cloud.google.com/apis/credentials/consent?project=jagyyaand
- API Credentials: https://console.cloud.google.com/apis/credentials?project=jagyyaand

---

**What to do right now**: Add `danklunawada@gmail.com` as a test user (takes 2 minutes)

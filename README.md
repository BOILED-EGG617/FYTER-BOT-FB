# Facebook Group Helper Bot (Template)
Credit: Script edited by RAVI KING

Important:
- This repository contains a safe template showing how to interact with Facebook Graph API and how to restrict commands to a single admin user.
- It does NOT provide or support automated friend-adding, forced nickname locks, or other actions that violate Facebook policies or user privacy.
- Always follow Facebook Platform Policies and get proper permissions & app review if needed.

Files included:
- fb_group_bot.py         -> The main Flask app / webhook / admin command endpoint
- requirements.txt        -> Python dependencies
- .env.example            -> Example environment variables

Quick setup (local, development):
1. Copy .env.example to .env and fill the values:
   - FB_GROUP_ID: your group's numeric ID
   - FB_ACCESS_TOKEN: long-lived access token with proper permissions
   - ADMIN_FACEBOOK_ID: your numeric facebook id only (bot will accept commands only from this ID)
   - FB_VERIFY_TOKEN: a string you choose; used by Facebook to verify webhook
   - ADMIN_COMMAND_SECRET: secret string used to protect the /command endpoint

2. Install dependencies:
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

3. Run the Flask app:
   export FLASK_ENV=development
   flask run --host=0.0.0.0 --port=5000
   or
   python fb_group_bot.py

4. Setup Facebook App & Webhook:
   - Create a Facebook App at developers.facebook.com
   - Request needed permissions (groups_access_member_info, pages_manage_posts, etc.). Many group-level permissions require review or may not be available for arbitrary apps.
   - In your App -> Webhooks, subscribe to Group events and set the callback URL to `https://<your-host>/webhook` and the verify token to the FB_VERIFY_TOKEN value.
   - When a webhook event is sent, inspect the payload structure and adapt `fb_group_bot.py` parsing logic accordingly.

5. Sending admin commands:
   - Call POST /command with JSON:
     {
       "admin_id": "YOUR_FACEBOOK_ID",
       "secret": "YOUR_ADMIN_COMMAND_SECRET",
       "command": "post",
       "args": "Hello group"
     }
   - Only requests that include the correct secret and admin_id will be accepted.

Notes & Warnings:
- Posting too frequently or automating messages at tight intervals (like every 10 seconds) is likely to be treated as spam by Facebook. Use reasonable intervals and get user consent.
- Programmatically adding friends or forcibly changing other users' profile settings is not supported by the Graph API and is disallowed.
- Keep your ACCESS_TOKEN and secrets safe. Do not commit `.env` to source control.
- This template is for educational / admin-help purposes. Modify it responsibly.

If you want, I can:
- Help adapt the webhook payload parsing to the exact payload your app receives (share a sample webhook JSON).
- Show how to deploy this safely on Heroku/GCP/AWS and configure HTTPS.
- Add an APScheduler example for polite scheduled posts (with rate limits and admin approval).
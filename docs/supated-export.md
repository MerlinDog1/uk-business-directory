# Private SUPATED customer export

The helper reads the Supabase project URL and public client key from `~/.supated-directory/supated-client-config.json`, outside this repository. On another computer, create that private file with the shape `{"url":"https://YOUR-PROJECT.supabase.co","key":"YOUR-PUBLIC-CLIENT-KEY"}` using your application's existing public client configuration. Do not put a service-role key in it.

Run this from the directory repository using Node.js:

```powershell
node tools/supated-export-server.cjs
```

Open [http://127.0.0.1:8766/](http://127.0.0.1:8766/) on the same computer. Sign in with your SUPATED account and choose **Sign in and save customers**. The page displays the exact saved path. Files are written under your user profile in `.supated-directory`, outside this public repository. Stop the helper with Ctrl+C when finished.

The page signs in directly to the SUPATED Supabase project using its existing public application key. The password and access token remain in page memory and are not saved. It requests only company, postcode and phone number, in pages of up to 1,000, using the account's existing access policies. It checks the server-reported total before saving; a failed, incomplete, or empty read does not create an export. The loopback-only helper receives those customer fields only to save the file; it does not log them. Treat exports as private and do not commit them or publish them.

Access depends on the SUPATED account's current database permissions; this helper does not change or bypass them. The live sign-in and export require valid credentials and must be verified with an authorised account.

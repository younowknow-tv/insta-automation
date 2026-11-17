# git: which GitHub account pushes this repo

Two accounts are logged in on this Mac: younowknow-tv (this repo) and dixitgurv
(the other automation work). Plain git push used to grab whichever one the
keychain answered with, and failed with 403.

The remote carries the username, so credentials are looked up per account:

    origin = https://younowknow-tv@github.com/younowknow-tv/insta-automation.git
    git config credential.https://github.com.username younowknow-tv   (local only)

For the other repo, do the same with its own account:

    git remote set-url origin https://dixitgurv@github.com/<owner>/<repo>.git
    git config credential.https://github.com.username dixitgurv

If a push ever asks for a password again, the keychain entry for that username
is missing. Restore it without printing the token:

    printf 'protocol=https\nhost=github.com\nusername=<acct>\npassword=%%s\n\n' \
      "$(gh auth token --user <acct>)" | git credential-osxkeychain store

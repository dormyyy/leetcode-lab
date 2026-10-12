# Accepted solutions from the browser

AlgoVault writes Accepted submissions to `browser-sync/{number}-{slug}/`.
The sync workflow imports them into `problems/`, preserves existing notes, and
updates the progress table. Configure the extension with
[`docs/algovault-settings.json`](../docs/algovault-settings.json).

This folder is an archive of the original submitted code. The C++ solution used
locally may also contain standard-library includes supplied by the local runner.
GitHub does not automatically update a local checkout; use `git pull` to fetch
new solutions from the browser.

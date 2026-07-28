# Setup Guide — from zero to live website

Written for someone who has never deployed a website. You will not need to
install anything or use a command line. Everything happens in your web
browser, and the whole setup takes about 20–30 minutes. After that, daily
publishing is a single file edit.

**The idea in one sentence:** GitHub stores your site's files, and every time
`data.json` changes, GitHub automatically rebuilds the site and publishes it
to your domain.

---

## Part 1 — Put the site on GitHub (~10 min)

1. Go to **github.com** and create a free account (if you don't have one).
2. Click the **+** in the top-right corner → **New repository**.
   - Repository name: `machine-speed` (or anything you like)
   - Visibility: **Public** (required for free GitHub Pages hosting;
     everything in this folder is meant to be public anyway)
   - Don't tick any of the "initialize" checkboxes.
   - Click **Create repository**.
3. Unzip `machine-speed-site.zip` on your computer.
4. On the empty repository page, click the **"uploading an existing file"**
   link. Drag the **contents** of the unzipped folder (not the folder itself)
   into the upload area: `build.py`, `data.json`, `README.md`,
   `SETUP_GUIDE.md`, `.gitignore`, and the `assets` and `archive` folders.
5. Click **Commit changes** at the bottom.
6. One folder can't be dragged in because it starts with a dot: `.github`.
   Add its file by hand:
   - In your repo, click **Add file → Create new file**.
   - In the name box type exactly: `.github/workflows/deploy.yml`
     (typing the `/` creates the folders).
   - Open `deploy.yml` from the unzipped `.github/workflows` folder in any
     text editor, copy everything, paste it in.
   - Click **Commit changes**.

## Part 2 — Turn on hosting (~5 min)

1. In your repository, go to **Settings** (tab at the top) → **Pages**
   (left sidebar).
2. Under **Build and deployment → Source**, choose **GitHub Actions**.
3. Go to the **Actions** tab. If GitHub asks you to enable workflows,
   click the green enable button.
4. In the left sidebar click **Build and deploy site**, then the
   **Run workflow** button → **Run workflow**.
5. Wait ~1 minute for the green checkmark. Your site is now live at
   `https://YOUR-USERNAME.github.io/machine-speed/` — open it and check.

From now on this happens automatically on every change; you never need to
press that button again.

## Part 3 — Connect your domain (~10 min, then up to a day for DNS)

Two halves: tell GitHub your domain, and tell your domain registrar where
GitHub is.

**On GitHub:**

1. **Settings → Pages → Custom domain**: type your domain, e.g.
   `machinespeed.techpointe.org`. Click **Save**.
2. Once the domain check passes (may take a few minutes to a few hours),
   tick **Enforce HTTPS**.

> **Your exact setup (machinespeed.techpointe.org on Squarespace):** because the
> site lives on a *subdomain*, you only need ONE DNS record — no A records.
> In Squarespace: **Domains → techpointe.org → DNS (or "DNS settings") → Add record**:
> Type **CNAME**, Host/Name **machinespeed**, Data/Target **velvethamm3r.github.io**.
> Save, then on GitHub set **Settings → Pages → Custom domain** to
> `machinespeed.techpointe.org`, wait for the green check, and tick **Enforce HTTPS**.
> The four A records below are only needed if you ever serve a bare domain like
> `techpointe.org` itself.

**At your domain registrar** (wherever you bought the domain — the steps are
the same everywhere; the menu is usually called "DNS", "DNS settings", or
"Manage DNS". On Squarespace it's **Domains → your domain → DNS**):

3. Add a single **CNAME** record on `techpointe.org`:
   - Host/Name: `machinespeed`
   - Value/Target: `YOUR-USERNAME.github.io` (your GitHub username, then
     `.github.io` — nothing else, no `https://`, no path)

   Because this is a subdomain, that one CNAME record is all you need. The four
   `185.199.x.x` A records are only for a bare apex domain like `example.com`
   — you do not need them here.

DNS changes usually take effect within an hour but can take up to 24.

**Last step — tell the site its own address:**

5. Already done — `SITE_URL` at the top of `build.py` is set to
   `https://machinespeed.techpointe.org`, and every build writes that domain
   into `dist/CNAME` so a deploy can never silently drop it.

That's it. The site rebuilds itself and you're live.

## Part 4 — Daily publishing

The only file that ever needs editing is **`data.json`**. Each run:

1. Update `updatedISO`, `updatedDisplay`, `judgmentNote`, `internalNote`.
2. Add new `items`, remove ones older than 7 days.
3. Update `watchlist` rows that changed.
4. Add today's line to the top of `archives`:
   ```json
   { "date": "2026-07-24", "file": "archive/machine-speed-2026-07-24.html",
     "items": 9, "note": "one-line summary of the day" }
   ```
5. Commit. Within a minute the site rebuilds, today's snapshot is saved to
   the archive automatically, and the live site and RSS feed update.

You can do this by hand (open `data.json` on github.com, pencil icon, edit,
commit) — but the natural setup is to have your daily Cowork run do it: give
it access to the repository and ask it to update `data.json` with the day's
verified items, following the format of the existing entries, and push the
change. Everything downstream is automatic.

## If something goes wrong

- **Site didn't update after a change** → Actions tab: the latest run shows
  a red ✗ if the build failed, and clicking it shows why. The most common
  cause is a typo in `data.json` (a missing comma or quote). Fix and commit
  again.
- **Domain shows a 404 or certificate warning** → DNS is usually still
  propagating; wait an hour and try again. Check Settings → Pages shows a
  green check next to your domain.
- **Want to preview a change before it goes live?** Edits to `README.md` or
  this guide don't affect the site. For content, small `data.json` edits are
  low-risk: if a build fails, the live site simply keeps showing the last
  good version — a broken build never takes the site down.

## Later, if you outgrow this

Cloudflare Pages (see README.md) is a drop-in alternative host with faster
global delivery and per-commit previews; the repo works there unchanged.
You don't need it to start.

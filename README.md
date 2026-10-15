# Material Girl, Immaterial World

Link-in-bio site: https://brookebein.github.io/links/

The site is published by GitHub Pages from `main` and the repository root.

## Refreshing essays

The **Update link-in-bio** workflow runs daily at **15:17 UTC / 08:17 America/Phoenix** (`17 15 * * *`). It can also be run manually from the Actions tab. GitHub may delay scheduled runs, and schedules in inactive public repositories can be disabled after 60 days of inactivity.

The updater checks the latest 50 entries in Brooke's public Substack archive. For posts marked `audience: everyone` whose slugs are absent from `posts.json`, it generates an image tile, prepends a link to `index.html`, and records the slug. Existing tiles remain unchanged. New essays appear after a successful scheduled or manual refresh and Pages deployment; publication is not immediate.

Dependencies are Python 3.12, Pillow, and NumPy. The workflow uses its temporary GitHub token with `contents: write` and `pages: write` only in the update job; no personal token or repository-wide default write permission is required.

`python3 update.py --no-push` changes local site files without committing or pushing. The workflow then commits changed site files and explicitly requests a Pages rebuild, because pushes using `GITHUB_TOKEN` do not trigger branch-based Pages builds.

## Hub pages

The `/reels`, `/posts` and `/notes` pages are built from JSON by `build_hubs.py`. See `HUBS.md`.

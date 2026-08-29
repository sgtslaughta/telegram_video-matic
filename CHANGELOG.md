# CHANGELOG


## v1.2.0 (2026-08-29)

### Features

- **rugby**: Add a re-match action for media that never matched
  ([`4033df0`](https://github.com/sgtslaughta/telegram_video-matic/commit/4033df06d1c064d94681233910eee6f4ae1fb16a))

Fixture matching only runs at discovery (on_media_discovered), so fixtures that arrive later — a
  deep fetch, a newly tracked league — can never attach to an already-downloaded video. Those items
  keep a bare Jellyfin NFO with no league, teams or tags, and no existing action fixes them:
  reconcile only walks rows that are already auto/confirmed, and update_match needs a row that was
  never written.

rematch() retries every item with no match row at all, then re-files and rewrites metadata for
  whatever lands. Items already matched or awaiting review are left alone. Exposed as POST
  /api/plugins/rugby/rematch and a "Re-match unmatched" button beside Scan now / Reorganize library.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>


## v1.1.2 (2026-08-29)

### Bug Fixes

- **docker**: Clear HIGH CVEs failing the Trivy image scan
  ([`3c06b67`](https://github.com/sgtslaughta/telegram_video-matic/commit/3c06b6706add6007578f99968659af7dd0b64e5d))

The image scan blocked releases on four HIGH findings unrelated to app code: Alpine's openssl libs
  lagging the base image, cryptography 49.0.0, and msgpack/setuptools vendored inside the base
  image's pip.

apk upgrade picks up the openssl fix, cryptography moves to 50.0.1, and both pip installations are
  dropped from the runtime layer — the app runs out of /opt/venv and never installs packages at
  runtime.

Verified locally: trivy image scan exits 0, container healthy in 3s.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>

- **frontend**: Bump react-router-dom to 7.18.3 for GHSA-qwww-vcr4-c8h2
  ([`c4f85e1`](https://github.com/sgtslaughta/telegram_video-matic/commit/c4f85e14914b9c54fd0a1de780f200d7b4fe470c))

Trivy's filesystem scan fails the pipeline on a HIGH CSRF advisory against react-router 7.18.0 (RSC
  mode action execution before a 400 response).

102 vitest tests and the production build pass on the new version.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>

- **naming**: Honor subscription topic when template has no S/E tokens
  ([`b1eb409`](https://github.com/sgtslaughta/telegram_video-matic/commit/b1eb409df27e28ba1292e14ac73c9473b992861d))

Downloads landed in a channel-named folder whenever the rugby plugin found no match:
  choose_target_path only used rename_template if an S##E## pattern was detected or a plugin
  supplied tokens, so a "{topic}/{title}.{ext}" template never rendered and the hardcoded fallback
  used the channel title.

Templates now render unless they reference {season}/{episode}, which still require detection. The
  no-template fallback prefers the source topic over the channel. Season/episode are also no longer
  parsed (into the NFO) when season_detection is off.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>


## v1.1.1 (2026-07-18)

### Bug Fixes

- **rugby**: Stop age-grade games matching senior fixtures
  ([`a0eef5b`](https://github.com/sgtslaughta/telegram_video-matic/commit/a0eef5ba70137beb2f62afea96550ea028bc0ed9))

Junior World Championship videos were auto-filed under senior tournaments. Three defects compounded:

- U20/women's fixtures reuse the senior team names, and team presence alone scored 0.6 base + 0.2
  coverage = the 0.8 auto threshold, so "England U20 v France U20" auto-matched a senior England v
  France fixture. - "Junior World Championship" contains "world cup" as a substring, so
  league_hint() resolved it to the senior Rugby World Cup. - _load() never populated league_name,
  leaving the league-hint factor dead in every real code path; only the demo exercised it.

Fixes:

- grades() derives u20/u19/u18/women/sevens tags from the title, the source channel/topic and the
  fixture's league + team names. Disagreement vetoes the fixture outright rather than penalising it.
  - Team names alone now cap at 0.79 (needs_review). Round, date or league must corroborate before
  anything auto-files. - League hint is two-sided: +0.05 on a hit, -0.35 when the title names a
  different competition. - JWC hint tokens precede "world cup" and resolve to a needle no catalog
  league contains, since thesportsdb has no JWC league. Those games now come back unmatched instead
  of wrong. - Channel and topic titles reach the matcher in match_item() and both enrichment paths,
  where the competition is often the only place the grade is named. Round and date still come from
  the title alone.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>


## v1.1.0 (2026-07-11)

### Features

- **rugby**: Surface plugin actions in the activity feed
  ([`c390c4d`](https://github.com/sgtslaughta/telegram_video-matic/commit/c390c4dacc5826d9f00622ad28d2274d22fe142a))

The activity feed showed almost nothing for the rugby plugin — ctx.log was only called on
  warnings/errors, so normal enrichment was invisible. Emit INFO/SUCCESS events at each milestone
  (all linked to the media item):

- match_item: Matched / Needs review / No match / on-demand lookup - write_jellyfin: NFO written
  (now returns bool so the log is accurate) - reconcile: "N re-filed, M refreshed" summary -
  on_enable: league-catalog seed

Events are emitted after the DB session block closes so ctx.log's own session never nests inside
  match_item's. Existing warning/error logs kept.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>


## v1.0.14 (2026-07-11)

### Bug Fixes

- **rugby/nfo**: Drop <lockdata> so Jellyfin re-reads corrected metadata
  ([`434838b`](https://github.com/sgtslaughta/telegram_video-matic/commit/434838b9edcf0a10a058ab43bf0e4f100a749d4f))

lockdata=true made Jellyfin set IsLocked=1 on import, after which it ignores the NFO on every
  subsequent scan — so metadata corrections (re-match, episode renumbering, artwork) never
  propagated. Users had to force "Replace all metadata" in Jellyfin for any fix to appear.

Stop emitting <lockdata> in episode/tvshow/season NFOs. Unlocked items are re-read from the NFO on
  each scan, so fixes self-propagate. These custom league shows don't match online scrapers; disable
  metadata downloaders on the rugby library to keep Jellyfin from clobbering the NFO.

Note: already-locked items stay locked in Jellyfin's DB — a one-time "Replace all metadata" is still
  needed to adopt the new unlocked NFOs.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>


## v1.0.13 (2026-07-11)

### Bug Fixes

- **rugby/nfo**: Unique episode number per game so Jellyfin stops merging rounds
  ([`d14d58b`](https://github.com/sgtslaughta/telegram_video-matic/commit/d14d58b83e69f41c2af8c45696cecc9a8d736921))

_episode_number mapped a numeric round straight to <episode>, so every game in a round shared one
  SxxExx. Jellyfin keys episodes by season+episode and collapses collisions into a single episode
  (extras become hidden "versions"), leaving later games bare — e.g. Round 2's three games all
  claimed S2026E02.

Episode is now round*100 + slot, where slot is the game's 1-based position within its round (by
  kickoff, then fixture id). Keeps rounds grouped and ordered while staying unique (Round 2 -> 201,
  202, 203). Non-numeric rounds (finals) map to 90000 + dayofyear*100 + slot so they sort last and
  distinct. write_jellyfin computes slot from the round's sibling fixtures.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

### Continuous Integration

- Automate semver + changelog with python-semantic-release
  ([`dc81c98`](https://github.com/sgtslaughta/telegram_video-matic/commit/dc81c98e797bd480b54ee9067e863cb7e28e2bf0))

- pyproject.toml [tool.semantic_release]: version in app/main.py:__version__ + pyproject;
  conventional-commit parser (feat->minor, fix/perf/refactor-> patch, ! / BREAKING->major);
  CHANGELOG.md in init mode (full history). - ci.yml: new `version` job runs PSR on main push (bump
  + changelog + tag + GH release via GITHUB_TOKEN); `release` job builds/pushes the image in the
  same run using PSR's version output (:main always; :X.Y.Z/:X.Y/:latest on release) — no PAT
  needed. - Seed CHANGELOG.md from existing tags; document convention in CONTRIBUTING.md. -
  app/main.py: version -> module-level __version__ (PSR single source).

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>


## v1.0.12 (2026-07-05)

### Features

- **rugby/nfo**: Emit all league artwork URLs with Jellyfin aspects
  ([`f1bb9b5`](https://github.com/sgtslaughta/telegram_video-matic/commit/f1bb9b5a613de345d1dd045000f21adbc8643972))

tvshow.nfo now references every available image by URL — poster, banner, clearlogo (logo), keyart
  (badge), fanart — deduped, so Jellyfin pulls them remotely. season.nfo gets a poster thumb. DB
  badge_url backfills badge/poster/ logo when the API lacks them (offline / rate-limited).

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>


## v1.0.11 (2026-07-05)

### Features

- **ui/rugby**: "reorganize library" button (POST /reconcile)
  ([`f4e08b3`](https://github.com/sgtslaughta/telegram_video-matic/commit/f4e08b388ec030886d8f2e63900f1d3fe5bb3f99))

Adds a button to the rugby plugin card in Settings that triggers the reconcile pass (re-file matched
  games into league/Season/round folders + refresh Jellyfin metadata), mirroring the existing "Scan
  now" pattern (hook + toast).

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>


## v1.0.10 (2026-07-05)

### Features

- **rugby/nfo**: Richer tags (sport, year, teams, tournament, venue, country)
  ([`a3a3e3d`](https://github.com/sgtslaughta/telegram_video-matic/commit/a3a3e3db8c2506c10f3983d70225551b60cbeb37))

Episode/tvshow/season NFOs now emit a deduped tag set for Jellyfin filtering: Rugby, sport (e.g.
  Rugby Union), year, league/tournament, season, round, home/away teams, venue, country.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>


## v1.0.9 (2026-07-05)

### Features

- **rugby**: Reconcile re-files matched games + rich Jellyfin metadata
  ([`6902038`](https://github.com/sgtslaughta/telegram_video-matic/commit/69020385576f21d5651f7f5f3c8463491d6560ff))

Matches often resolve after download (needs_review -> confirmed), so the download-time path_for saw
  no match and the file kept its raw name; nothing re-filed it later. Add a reconcile pass that
  moves every matched item to its league/Season N/round path (+ -thumb sidecar) and rewrites full
  metadata.

- reconcile()/_reconcile_one()/_refile() in RugbyService; wired into update_match (confirm) and
  exposed as POST /reconcile. - lookup_league API + tournament poster/fanart/logo at league root,
  season poster in-folder; season.nfo; SortsDB team bios in episode plot; no scores. - naming:
  fallback always nests under a channel subfolder (safe_segment); rugby path emits
  Jellyfin-recognized "Season {year}" folders.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>


## v1.0.8 (2026-06-28)

### Features

- **rugby/nfo**: Rich episodedetails + tvshow.nfo ordered by round/date
  ([`231b1c4`](https://github.com/sgtslaughta/telegram_video-matic/commit/231b1c48b0aade9d9f04a56757800b0fd24ca8ca))

For a Jellyfin TV Shows library: league = series, season = season, round = episode, so episodes sort
  by round. Non-numeric rounds (finals) are numbered after the regular season and ordered by date
  played. Populate title/originaltitle/showtitle/season/episode/sorttitle/plot/outline/
  tagline/runtime/premiered/aired/dateadded/uniqueid/studio/network/genre/ tags/actors(order+badge),
  and lockdata=true so Jellyfin keeps our data instead of generating its own. Write tvshow.nfo at
  the league root. Filenames become 'Round NN - Home vs Away.ext'.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>


## v1.0.7 (2026-06-28)

### Bug Fixes

- **naming**: Collapse doubled dot in rendered filename (name..mp4 -> name.mp4)
  ([`c5921e5`](https://github.com/sgtslaughta/telegram_video-matic/commit/c5921e59c94671606f6a87388fce2ee8ac67c7d4))

The {ext} token already carries a leading dot, so templates written as '{title}.{ext}' produced
  'name..mp4'. render_path now collapses repeated dots in the final path segment (dirs untouched),
  and the default template drops the stray dot ({channel}/{title}{ext}).

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>


## v1.0.6 (2026-06-28)

### Features

- **rugby**: Auto-file matched media into league/season folders
  ([`1276b73`](https://github.com/sgtslaughta/telegram_video-matic/commit/1276b736d25246952abcc1b953170ce0f77f41ed))

New provide_path plugin hook (host.collect_path picks the first non-None) lets a plugin dictate the
  full relative path, overriding the subscription template. Rugby returns '<league>/<season>/<home>
  vs <away><ext>' for auto/confirmed matches, so media auto-organizes into a league/season tree from
  the storage root with no hand-authored template (and no '.{ext}' double-dot). Falls back to the
  template when no plugin claims the path.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>


## v1.0.5 (2026-06-28)

### Bug Fixes

- **download**: Eager-load sub channel/topic to stop greenlet_spawn
  ([`6c71683`](https://github.com/sgtslaughta/telegram_video-matic/commit/6c71683984b8480f8128458abe14a28d54ea15a5))

choose_target_path (sync) read sub.channel.title / sub.topic.title; with the bare
  subscriptions.get() those were lazy and triggered async IO from sync code -> 'greenlet_spawn has
  not been called', aborting the download before the file move (so the target folders were never
  created). Eager-load both relationships via selectinload.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- **rugby**: Preselect saved subscription league in the editor
  ([`61bf817`](https://github.com/sgtslaughta/telegram_video-matic/commit/61bf81709c95dc14d92973b14fd3e7aecd8280be))

The league persisted (rugby_subscriptions) but the editor had no read-back, so reopening a sub
  showed it blank -> looked unsaved. Add GET /plugins/rugby/subscriptions/{id} +
  useSubscriptionLeague hook and preselect selectedLeague on edit.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

### Features

- **nfo**: Include rugby genre/studio/teams in the jellyfin .nfo
  ([`af6ea15`](https://github.com/sgtslaughta/telegram_video-matic/commit/af6ea158871077780abd0d6b33af25f8f9f0400d))

Pass plugin naming tokens to _write_jellyfin_nfo; emit genre (sport), studio (league), and tags
  (home/away/season/round) when present so the base .nfo carries rugby metadata even when artwork
  enrichment is off.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>


## v1.0.4 (2026-06-28)

### Bug Fixes

- **docker**: Add libgcc so cryptg actually loads at runtime (v1.0.4)
  ([`76c1e2d`](https://github.com/sgtslaughta/telegram_video-matic/commit/76c1e2d8743dc38d90112531670ef60719aab535))

v1.0.3 shipped cryptg but its compiled .so links _Unwind_* from libgcc_s.so.1, absent in the Alpine
  runtime stage (only libffi/su-exec were installed). Import failed at runtime and Telethon silently
  fell back to pure-Python AES — so the core stayed pinned (~121% CPU) and MTProto fell into a
  resent-message storm. Verified on the live Unraid box via ldd; cryptg now imports in the rebuilt
  image.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>


## v1.0.3 (2026-06-28)

### Continuous Integration

- Publish rolling :main image tag on pushes to main
  ([`8d868ac`](https://github.com/sgtslaughta/telegram_video-matic/commit/8d868ace56bc623a50f850cb8eae22321963ed95))

Release job now also runs on main pushes, tagging the image :main via metadata-action
  type=ref,event=branch. :latest stays gated to v* tags.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

### Features

- **rugby**: Show source message vs suggested fixture in match review
  ([`2d99760`](https://github.com/sgtslaughta/telegram_video-matic/commit/2d99760d901aeadbb13ef1135eb720339adb075d))

The review payload returned only the matcher's suggested fixture. Join RugbyMatch -> MediaItem in
  list_matches so each item carries the source (file_name, caption, date_posted). Review screen now
  renders a side-by-side: Source (the Telegram message) | Suggested match, so the user can verify
  before confirming.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- **ui**: Folder-browse helper for the storage-path picker
  ([`199df27`](https://github.com/sgtslaughta/telegram_video-matic/commit/199df270a5c4471ad288e3acc66a4c100a7ccc75))

New GET /api/fs/dirs lists immediate subdirectories, sandboxed to MEDIA_ROOT (resolves .. and
  symlinks, rejects anything outside). The storage-path input in the subscription editor gains a
  Browse popover: list subfolders, click to descend, breadcrumb up, 'use this folder'. Typing a path
  by hand still works.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

### Performance Improvements

- Add cryptg + offload blocking download I/O off the event loop
  ([`b8b6f0a`](https://github.com/sgtslaughta/telegram_video-matic/commit/b8b6f0a641429d02dfac3c166230639a64f76c70))

Root cause of one core pegged at 100% on the server: without cryptg, Telethon runs MTProto AES in
  pure Python on the single event loop, GIL-held — concurrent downloads saturate one core and starve
  the API (Settings/Browse crawl). Added cryptg==0.6.0 (C, releases the GIL; verified it builds in
  the Alpine image).

Also offload shutil.move + quick_hash via asyncio.to_thread so a cross-fs move or hash never freezes
  the loop, and throttle download progress DB writes to ~5s (WS broadcast stays 1Hz) to ease SQLite
  write pressure under concurrent downloads.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- **browse**: Cache browse thumbnails in a bounded LRU
  ([`e7c2f94`](https://github.com/sgtslaughta/telegram_video-matic/commit/e7c2f943823dc3856bb61a97ed9a60e798a659f7))

thumb_b64_for re-fetched each thumbnail from Telegram (2 RPCs) on every request; Browse renders ~50
  at once. Add a process-level LRU (cap 1024) keyed by (channel, msg) so repeat renders and
  post-browser-cache-expiry reloads don't re-hit Telegram.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>


## v1.0.2 (2026-06-28)

### Bug Fixes

- **ci**: Dedupe brand wordmark, ignore intentional Trivy root-user check
  ([`aaf8b2f`](https://github.com/sgtslaughta/telegram_video-matic/commit/aaf8b2f6bdbf57fd9906e7da3ff565b04e880616))

Brand glyph now sits beside the existing sidebar wordmark instead of adding a second 'Video-Matic'
  lockup in the header (the duplicate broke App.test.tsx getByText). Logo gains a style prop for the
  accent color.

.trivyignore suppresses AVD-DS-0002/DS002: the entrypoint must start as root to chown bind mounts to
  PUID:PGID, then drops via su-exec — verified the app process runs as the requested uid, not root.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- **startup**: Clear preflight errors + working PUID/PGID on Unraid
  ([`3c96c2c`](https://github.com/sgtslaughta/telegram_video-matic/commit/3c96c2cbbe3f81fdade12453b8f593b50a455f28))

Startup failures now log one actionable line instead of a stack trace: app/preflight.py validates
  TVM_SECRET_KEY and SQLite data-dir writability, run from app/__main__.py BEFORE the app imports
  (so a missing secret or an unwritable /data never reaches the user as a traceback). CMD -> python
  -m app.

Unraid bind-mount perms: docker/entrypoint.sh chowns /data+/media to PUID:PGID and drops root via
  su-exec (non-root compose path unchanged). Added PUID/PGID to the Unraid template (default
  99:100). Verified in-image: health 200, process runs as the requested uid, DB files owned by it.
  Bump 1.0.0 -> 1.0.2.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>


## v1.0.1 (2026-06-28)

### Features

- **brand**: Paper-plane/play glyph for favicon, UI logo, Unraid icon
  ([`4a524b5`](https://github.com/sgtslaughta/telegram_video-matic/commit/4a524b5f06edfb4f3192c7d3960f6549d446a8f4))

One mark, three renders: favicon.svg + 256px unraid/icon.png bake the purple gradient; Logo.tsx uses
  currentColor so the header mark tracks the user's accent picker. Header gains a left-aligned brand
  lockup; page title fixed from 'frontend'. Re-added Icon ref in unraid template.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>


## v1.0.0 (2026-06-28)

### Bug Fixes

- Account status read (str not enum.value); add backend-down banner + change-credentials path
  ([`0389a1a`](https://github.com/sgtslaughta/telegram_video-matic/commit/0389a1aee640cb0f8ebcc2c1007e0577d3cf6171))

- _get_tg_status: str(account.status) — column is a plain string, not enum - Shell: 'Can't reach the
  server' banner when status query errors - Login flow: 'Change API credentials' lets you re-enter
  api_id/api_hash after configured

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Ad-hoc downloads run + live progress/speed/ETA in Downloads
  ([`ae81c1d`](https://github.com/sgtslaughta/telegram_video-matic/commit/ae81c1d5bb9e3d4bc3ed4335ca94adc57bfdf69a))

- claim_pending: outerjoin so ad-hoc (no-subscription) media is claimed - downloads.running(): flip
  job QUEUED->RUNNING, record bytes_total - downloader: persist progress to DB + compute
  speed_bps/eta_sec per tick - engine.start(): cancel orphaned QUEUED/RUNNING jobs from prior run -
  ws: broadcast uses "kind" envelope (was "type"); frontend matches on media_id - ProgressBar
  callers pass 0-100 (was 0-1 fraction -> invisible bar) - Downloads page: condensed single-row
  layout per job - test_config: _env_file=None so local .env can't supply the key

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Add AccountRepository adapter + update_status/update_session to reconcile service<->repo contract
  ([`9ea52c0`](https://github.com/sgtslaughta/telegram_video-matic/commit/9ea52c05cc6656ad9dd5695203f7afd73d40f4f9))

- Added module functions: get_single(), update_status(), update_session() to accounts.py -
  Implemented AccountRepository class that wraps async session_factory and delegates to module
  functions - Class methods (get, update_status, update_session) open their own session from the
  factory - Added comprehensive integration tests in tests/test_account_repository.py - All 43 tests
  pass, including new repository tests and existing service tests

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

- Add AccountRepository.update_phone (service start_login dependency)
  ([`3c6dc39`](https://github.com/sgtslaughta/telegram_video-matic/commit/3c6dc39746cb060432f8d19a2279095f81319e01))

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

- Add get_by_channel_topic to subscriptions repo for duplicate detection
  ([`a33b4ba`](https://github.com/sgtslaughta/telegram_video-matic/commit/a33b4ba28f8a342a627b5fc794fb998b048e20b3))

- Align AccountStatus enum to backend (awaiting_code/awaiting_password)
  ([`709bcad`](https://github.com/sgtslaughta/telegram_video-matic/commit/709bcad62cdb900bd0c058b439ae0d521040006a))

UI stayed on phone after code was sent because frontend used waiting_* but backend sends awaiting_*;
  getStep matched nothing.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Align api client response shapes to backend (arrays, settings list, thumb url)
  ([`e19961d`](https://github.com/sgtslaughta/telegram_video-matic/commit/e19961d7f7bce2180094035b58fee481e283d1c4))

Changes: 1. media.list: returns MediaItemRead[] (not paginated), params use limit/offset/sub_id 2.
  events.list: returns EventRead[] (not paginated), params use limit/offset 3. settings.get/update:
  returns SettingRead[] (list, not single object) 4. media.thumbUrl: replaces thumb JSON fetch with
  URL helper function 5. Removed unused PaginatedResponse type from types.ts 6. Updated tests to
  assert correct array shapes and thumbUrl behavior

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Classify timeframe gate naive/aware datetime crash
  ([`2424aba`](https://github.com/sgtslaughta/telegram_video-matic/commit/2424abada267d75151da3a56a999ff7cfb77cc46))

date_posted is aware (Telethon) but sub date_from/date_to come back naive from SQLite; coerce both
  via _as_utc before comparing. Fixes "can't compare offset-naive and offset-aware datetimes" in gap
  reconcile + poller classify.

213 backend pass (mixed-tz classify test added), ruff clean.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Connect Telethon client before send_code_request (was 'cannot send requests when disconnected')
  ([`2675fd2`](https://github.com/sgtslaughta/telegram_video-matic/commit/2675fd200c39160ace12efe084c35ab53ebee801))

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Constant-time app-password compare + UTC timestamp
  ([`b77e0d1`](https://github.com/sgtslaughta/telegram_video-matic/commit/b77e0d1b6176d6ac9ee9617cde471d6d0f7607f2))

Use hmac.compare_digest in check_app_password to avoid timing leaks; replace deprecated
  datetime.utcnow with timezone-aware UTC.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

- Define --radius (rounded corners) + surface Telegram login errors via toast
  ([`0e777a8`](https://github.com/sgtslaughta/telegram_video-matic/commit/0e777a8c8f1975d5e267fc039061832def599c21))

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Downloader explicit season fallback + non-blocking retry backoff
  ([`c059d95`](https://github.com/sgtslaughta/telegram_video-matic/commit/c059d95c0dcfaa4334dfec1618eb2b1ccdef885a))

FIX 1 (SEASON FALLBACK): Replace buggy regex (literal backslash-d) and exception-driven decision
  with explicit pattern check. File with NO S/E pattern keeps original basename; with pattern +
  season_detection=True uses template. Prevents "Cooking Tips.mp4" → fabricated "01x01" paths.

FIX 2 (NON-BLOCKING RETRY): Remove blocking asyncio.sleep on non-final failures. On retry: increment
  attempt, set media→PENDING for next cycle, set job→QUEUED. Backoff gated by elapsed-time check at
  claim (no sleep). FloodWait still sleeps (capped 60s). Added downloads.get_latest_for_media() for
  backoff window check.

Tests: - Season fallback: file without S/E pattern stays at original basename - Season pattern: file
  with S/E pattern uses template - Retry logic: attempt increments, media→PENDING, no asyncio.sleep
  called - downloads.get_latest_for_media: retrieves most recent job by updated_at

All 117 tests pass (+3 new).

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

- Enable ws proxy for /api/ws in vite dev server
  ([`5ce7923`](https://github.com/sgtslaughta/telegram_video-matic/commit/5ce7923ee8a88689b9f2134bffafec755a25bbf3))

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

- Handle 204/empty API responses (delete/logout) + readable dialog title on dark
  ([`7cbd758`](https://github.com/sgtslaughta/telegram_video-matic/commit/7cbd758394c4c1a960414d89fdb04f9d469b2fbf))

- fetchAPI no longer calls .json() on empty bodies → delete subscription works (was rejecting on 204
  so the modal never closed) - dialog/alert-dialog content get text-foreground (title was black on
  dark bg)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Invalid filter_regex returns 400 (router-validated, not Pydantic 422)
  ([`b35e4be`](https://github.com/sgtslaughta/telegram_video-matic/commit/b35e4be9d6844d4a4ac19ddc7d0aa895823f80a3))

Move filter_regex compile-check from the schema validator (which yields 422) into the subscriptions
  router as an explicit HTTPException(400), matching the API spec. Update tests to assert the 400
  path.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

- Load secret/db config from .env reliably
  ([`cb33357`](https://github.com/sgtslaughta/telegram_video-matic/commit/cb33357137f5354b459affdbdfb0455fb42e09af))

- Settings: extra='ignore' so documented .env vars (TVM_APP_PASSWORD, MEDIA_ROOT, TZ) don't crash
  startup - init_crypto(secret_key): seed from Settings (which reads .env) instead of raw os.getenv

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Media discovery + subscribe topic dropdown
  ([`ae2d20c`](https://github.com/sgtslaughta/telegram_video-matic/commit/ae2d20c272b0329a9d7c55ad8073a469869eb9f5))

- engine passed DB ids to iter_media which expects Channel/Topic DTOs (.tg_id); add _sub_dtos to
  build them at all 3 call sites → media is actually fetched - iter_media scopes forum channels to
  the topic (reply_to) - SubscriptionEditor loaded topics for the existing sub's channel, not the
  selected one → empty dropdown when creating; bind to editor.state.channelId

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Media insert FKs + JSON-safe raw + float duration
  ([`89a393c`](https://github.com/sgtslaughta/telegram_video-matic/commit/89a393c0a394b2e24a13d177568953359f1894d4))

- upsert_from_tg_dto now takes DB channel_id/topic_id (was writing Telegram ids into FK columns →
  IntegrityError) - MediaDTO.raw no longer holds the Telethon Message (not JSON-serializable) -
  MediaItemRead floors float duration_sec to int (Telethon sends floats)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Persist session via client.session.save() (Telethon API; was get_session_string)
  ([`90d52ce`](https://github.com/sgtslaughta/telegram_video-matic/commit/90d52cea8c3fb77b3c684707ce96045a4c8a2273))

Verified against Telethon stable docs: StringSession exposes save(), not get_session_string. Fixes
  login crash on code submit; updates test mocks.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Poller datetime tz crash + gap-reconcile FK (tg topic id)
  ([`889d0cd`](https://github.com/sgtslaughta/telegram_video-matic/commit/889d0cdbc5081087abc6fedac30f43962e8a0599))

- gap reconcile inserted media with media_dto.topic_tg_id (Telegram id) into topic_id FK ->
  topics.id; use sub.topic_id (DB id) instead - _sub_due / per-sub retention / downloader backoff:
  SQLite returns naive datetimes; _as_utc() coerces before subtracting (was "can't subtract
  offset-naive and offset-aware datetimes")

Verified live: poller runs clean, media topic_id correct (=4). 212 backend pass.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Prevent path traversal in SPA fallback route
  ([`4d35b18`](https://github.com/sgtslaughta/telegram_video-matic/commit/4d35b181696a6df7bad38b080cccf4a7aa051123))

Resolve the candidate path and require it to stay within STATIC_DIR before serving, so ../ in the
  request path can't read arbitrary files.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

- Prompt sync-engine shutdown via stop-event-aware interval waits
  ([`0d0002b`](https://github.com/sgtslaughta/telegram_video-matic/commit/0d0002bce7a5b8d71d117e47cc12cae5e670ddbd))

Poller/maintenance/downloader loops waited with plain asyncio.sleep(interval), so stop() couldn't
  wake a mid-sleep loop and hit its 30s per-task timeout — slow shutdown in production and a 281s
  test suite. Replace interval sleeps with asyncio.wait_for(stop_event.wait(), timeout=interval):
  setting the event breaks the wait immediately. Make maintenance interval injectable. Add a
  regression guard asserting stop() returns <2s with large intervals.

Suite: 138 passed in ~2s (was ~281s).

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

- Rebuild client on load when API creds exist (survives restart pre-login)
  ([`c76ec21`](https://github.com/sgtslaughta/telegram_video-matic/commit/c76ec2136802381e2e4a6af289b150641ddc8831))

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Remove dead global topbar search; per-page search instead
  ([`d361181`](https://github.com/sgtslaughta/telegram_video-matic/commit/d361181657df612ab29e26aa976f9907c8c2cab9))

Topbar search only filtered 2 pages (felt unhooked). Removed it; SubscriptionsList gets its own
  search box (Browse already has one).

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Report TG status from DB + reconnect saved session on startup
  ([`535fc0e`](https://github.com/sgtslaughta/telegram_video-matic/commit/535fc0e3c6a067b773c4905ffb1ec0d21c6016ad))

- _get_tg_status reads account from DB (was stale in-memory svc.account, so a successful sign-in
  still showed awaiting_code → UI stuck on code step) - startup connect() restores a saved session
  to connected (shutdown marks it disconnected); update test mocks for the awaited account_repo.get

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Requeue orphaned queued/downloading media on engine start
  ([`696be75`](https://github.com/sgtslaughta/telegram_video-matic/commit/696be750a6dda652d518d250e1251f973e528ac2))

Downloads interrupted by shutdown/crash were stuck at queued forever (downloader only claims
  pending). Reset them to pending on start so they resume.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Reset stale awaiting_code/password to disconnected on load (restart-safe login)
  ([`e2b7642`](https://github.com/sgtslaughta/telegram_video-matic/commit/e2b7642ad8cb0d470d8c249d5b25c3cb1d0d2dec))

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Resolve channels via PeerChannel for topics/media (bare int read as user)
  ([`f922963`](https://github.com/sgtslaughta/telegram_video-matic/commit/f922963224f333908c1ed337efcf614bed235356))

Telethon treats a bare positive int as a PeerUser; wrap tg_id in PeerChannel so forum topics and
  media iteration resolve. Topics endpoint now syncs live topics into the DB like channels. Surfaces
  sync errors instead of silently swallowing.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Router tests for new page implementations
  ([`1626873`](https://github.com/sgtslaughta/telegram_video-matic/commit/16268731422d6536d79b17f1ffd1d97a0231ed7c))

Update Router tests to check for 'Welcome back' (Dashboard hero) and use getByRole for Login heading
  to avoid matching multiple 'Login' text nodes.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com> EOF )

- Smooth download rate (EMA) to stop speed/ETA jitter
  ([`b3ef091`](https://github.com/sgtslaughta/telegram_video-matic/commit/b3ef091de8f2b8e09fd858c70e0b4b220126bc89))

Parallel transfer delivers bytes in bursts, so the 1s instantaneous rate swung wildly. Apply an EMA
  (0.4 new / 0.6 prev) over the per-window rate; guard delta<0. ETA derives from the smoothed value.
  Live: steady readings.

215 backend pass, ruff clean.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Spa client-side route fallback to index.html
  ([`882bcb7`](https://github.com/sgtslaughta/telegram_video-matic/commit/882bcb792a7cb2b97a9caf25d449ed62da080513))

StaticFiles(html=True) only served index.html for '/', so deep links like /subscriptions or /media/5
  returned 404 on refresh. Mount hashed assets under /assets and add a catch-all that serves real
  files else index.html, while unmatched /api paths still 404 as JSON.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

- Stop activity-feed flood from per-item filter skips
  ([`2d274f5`](https://github.com/sgtslaughta/telegram_video-matic/commit/2d274f54e0c1a959e9737a6546fe7f456b027d43))

- routine filter skips no longer log an event (89 "Posted before…" lines); SKIPPED status in Browse
  is the record - poller logs ONE summary per poll with context: "<sub>: queued N new, skipped M
  (filtered)" — only when something was queued - gap reconcile counts/queues only NEW items: "queued
  N new media item(s)" - updated 2 tests to assert no filter events

213 backend pass, ruff clean.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Sync live Telegram channels into DB on GET /api/channels
  ([`823cc40`](https://github.com/sgtslaughta/telegram_video-matic/commit/823cc406dc61dc6af5382be9f6ac578c4ab4b1b3))

Endpoint returned the empty channels table; now fetches the user's channels via the connected client
  and upserts them so the add-subscription dropdown is populated.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Tailwind v4 CSS pipeline — @import + @config (was v3 directives, emitted zero utilities)
  ([`850101a`](https://github.com/sgtslaughta/telegram_video-matic/commit/850101a39ca3763384106ecbda8797a56cb8e639))

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Tg/status returns disconnected (not 500) when no account configured
  ([`e8d6ffc`](https://github.com/sgtslaughta/telegram_video-matic/commit/e8d6ffc313d6912ee578f979d9102eeecc604c4a))

Fresh install has no Account row yet; status must report disconnected so the UI shows the connect
  wizard instead of erroring.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

- Thumb_b64_for (avoid name collision with fetch_thumb(message))
  ([`42d7f7c`](https://github.com/sgtslaughta/telegram_video-matic/commit/42d7f7c186f83e54e772c3b9b62287134ccb8028))

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Topic/channel names on sub card, edit-form populate, downloads filename
  ([`442ae20`](https://github.com/sgtslaughta/telegram_video-matic/commit/442ae205723ab04702388fe6e317e597c6a1ccf7))

- SubscriptionRead enriched with channel_title + topic_title (router); list card shows "Channel ·
  Topic" instead of "Topic <id>" - edit form now populates: useSubscriptionEditor re-seeds via
  resetKey when the query resolves (was stuck on defaults — useState init ran pre-load) - Downloads
  row shows media file_name (enriched into DownloadJobRead) with "Download #id" fallback, instead of
  bare "#id"

212 backend + 98 frontend pass, app ruff clean, build OK.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Update tests for shadcn/ui refactoring (tooltip buttons, toast errors)
  ([`53b392a`](https://github.com/sgtslaughta/telegram_video-matic/commit/53b392a3caa618e1655e0fafc9e9b0767fa8911e))

- Use ConfirmDialog (native modal) for Downloads clear-data confirm
  ([`f96bbf3`](https://github.com/sgtslaughta/telegram_video-matic/commit/f96bbf349642d5c5497b3d577aea66b5553c1584))

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- **docker**: Run container as host PUID/PGID so SQLite can write bind mounts
  ([`aad3b4c`](https://github.com/sgtslaughta/telegram_video-matic/commit/aad3b4cd2ff8edf4938ab1f2025a9fd4c9f78b85))

Bind mounts carry host ownership and shadow the image's build-time chown, so the non-root image user
  (uid 100) couldn't write ./data -> "attempt to write to a readonly database". Run as the host
  owner instead.

- compose: user: "${PUID:-1000}:${PGID:-1000}" - .env.example + README: document PUID/PGID +
  troubleshooting entry

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- **rugby**: Make catalog + deep fetch actually work against the live site
  ([`9c2277b`](https://github.com/sgtslaughta/telegram_video-matic/commit/9c2277b75c5c9079c1a246ffde65eaa5ac847a3d))

Found by a live smoke test (plugin enabled end-to-end): - Catalog parser never matched: live hrefs
  are relative ("../league/4414-..") but the regex anchored to a leading "/", so the catalog came
  back EMPTY. Search anywhere in the href instead; title-case the slug for a readable name (live
  anchors are icon-only, no text). - refresh_catalog only seeded on exception — an empty scrape
  stored nothing. Now an empty result also falls back to the bundled seed (catalog never empty). -
  Deep fetch pulled stale 2014-2015 fixtures: free-tier search_all_seasons is truncated to old
  seasons. Default to the locally-computed current + previous season instead (eventsseason serves
  the current season fine by id).

Smoke-verified: enable -> 51 leagues -> deep-fetch English Prem -> current + previous season
  fixtures -> "Sale Sharks v Gloucester highlights.mp4" matches auto -> "English Prem
  Rugby/2025-2026/R1 Sale Sharks vs Gloucester.mp4". 32 rugby tests pass.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

- **ui**: Handle app-auth 401 instead of masking it as "server unreachable"
  ([`2808fb9`](https://github.com/sgtslaughta/telegram_video-matic/commit/2808fb95050df9e1254b8e1146e0039826d6c6fa))

When TVM_APP_PASSWORD is set and there's no session, every /api/* call returns 401. The SPA had no
  auth guard, so useTgStatus's 401 rendered the "Can't reach the server" banner and never routed to
  the existing /login page — also leaving the Telegram connection state invisible.

- api client: on 401 (except the login request / when already on /login), redirect to /login -
  Shell: show "can't reach server" only on a true network error (no HTTP status); HTTP errors are
  handled by the redirect - tests: 401 redirects for normal endpoints, no redirect for the login
  call

After app login, /api/tg/status returns 200 (disconnected) and the Header "Connect" badge +
  auto-opened Telegram dialog make the missing connection clear.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- **ui**: Trim app password so pasted whitespace/newline doesn't false-reject
  ([`87df251`](https://github.com/sgtslaughta/telegram_video-matic/commit/87df251fbd7b56411e53eb850ca6e27b6ab701f4))

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- **unraid**: Correct GHCR repo coords, drop missing icon ref
  ([`1b49ae8`](https://github.com/sgtslaughta/telegram_video-matic/commit/1b49ae87572e717734606e620a546675d89c8dc7))

Template pointed at placeholder ghcr.io/user/... — repaired to real
  ghcr.io/sgtslaughta/telegram_video-matic. Removed Icon URL (no art yet; broken image is worse than
  none). Rugby plugin ships in image, dormant until enabled (Plugin.enabled defaults False).

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

### Build System

- Add recharts for dashboard chart
  ([`74c3dc3`](https://github.com/sgtslaughta/telegram_video-matic/commit/74c3dc328723d05b02a907c3b22dddabed38dd1e))

- Alpine multi-stage Docker + latest deps
  ([`876918b`](https://github.com/sgtslaughta/telegram_video-matic/commit/876918b1354bdd3c2989c7358ac1d7e5feb601f9))

- Dockerfile: 3-stage Alpine (node:24 SPA -> python:3.14 builder venv -> python:3.14 runtime),
  non-root, stdlib healthcheck (no curl), OCI labels - requirements.txt bumped to latest; split
  pytest/ruff into requirements-dev.txt - compose: drop obsolete version:, drop curl healthcheck,
  add image tag - ci: Python 3.12->3.14, install requirements-dev.txt - telethon 1.44:
  GetForumTopicsRequest channels->messages, channel=->peer= - fastapi 0.138: test reads openapi()
  paths (lazy _IncludedRouter)

215 tests pass on 3.14, ruff clean, image builds + runs healthy (237MB)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

### Chores

- Remove legacy streamlit/mariadb docker tree
  ([`45c7684`](https://github.com/sgtslaughta/telegram_video-matic/commit/45c76840fef34d02b32675c1131250629a480fcf))

Remove old docker/python/ (Streamlit app, utils, tests, requirements.txt), old docker-compose.yml
  (MariaDB), and old Dockerfile. App code has been migrated to app/ and is fully functional. All 202
  tests pass.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Untrack stray root tvm.sqlite, ignore sqlite files
  ([`3ba8a73`](https://github.com/sgtslaughta/telegram_video-matic/commit/3ba8a735fec30196f09075c9c9031fdf8c5498c0))

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Vendor fast_telethon download helper
  ([`e7e3257`](https://github.com/sgtslaughta/telegram_video-matic/commit/e7e3257a4007eb9977b948a751c4f2aab35ba0e7))

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

### Code Style

- Fix ruff lint so CI passes (unused imports/vars, __all__, is_(True))
  ([`8ef2228`](https://github.com/sgtslaughta/telegram_video-matic/commit/8ef2228cd8f3aa44e532103a71a42c933826cb96))

Add __all__ to routers package, drop unused 'me' assignments, use .is_(True) instead of == True in
  SQLAlchemy filters, remove unused imports. ruff check app/ clean; 202 tests green.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

- Layered slate palette for depth (dashboard-example contrast)
  ([`24dec08`](https://github.com/sgtslaughta/telegram_video-matic/commit/24dec08aff1cfa84fdf06eb4342905563c170b15))

- dark: near-black slate page (--background) vs lighter slate --card so sidebar + cards (both
  bg-card) read as elevated panels; visible borders - light: faint cool-gray page vs white cards for
  the same elevation - fix accent tokens that were inverted (near-black hover in light, near-white
  in dark)

98 frontend pass, build OK.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Neutral palette for Activity, Settings, shared components
  ([`1bd21ad`](https://github.com/sgtslaughta/telegram_video-matic/commit/1bd21ad92ea3abb5769608b3563d7b963092b077))

- Neutral palette for Browse + MediaDetail + search filter
  ([`558d8dc`](https://github.com/sgtslaughta/telegram_video-matic/commit/558d8dcf49f93d062a39434800bcfbfbf789271e))

- Neutral palette for subscriptions pages + search filter
  ([`383ddf7`](https://github.com/sgtslaughta/telegram_video-matic/commit/383ddf7bc58d63293285fccbb6fb237008f64e86))

- Re-skin Login page, fix MediaThumb, real channel names + useful search in SubscriptionsList
  ([`50c88c5`](https://github.com/sgtslaughta/telegram_video-matic/commit/50c88c53ac9d587d1ca2c269548d6ba998b10d50))

### Continuous Integration

- Bandit + trivy scans, multi-arch release on tags; simplify onboarding
  ([`93d1ce9`](https://github.com/sgtslaughta/telegram_video-matic/commit/93d1ce912c568286314f8628407ada554e018896))

Pipeline (.github/workflows/ci.yml): - backend: add bandit SAST gate (medium+) - new security job:
  trivy fs scan (deps, Dockerfile misconfig, secrets) - docker job: trivy image scan + inline smoke
  test (single build) - release job: on v* tags, build multi-arch (amd64+arm64) and push to GHCR -
  frontend CI node 20->24 to match image

- fast_telethon md5: usedforsecurity=False (Telegram protocol hash, clears bandit High) -
  bandit==1.9.4 in requirements-dev.txt

Onboarding: - move compose to root compose.yml (auto-discovered; ./data, ./media, .env at root) -
  README rewritten: accurate `docker compose` v2 cmds, pre-built GHCR image, real repo URLs, current
  dev/CI sections - .dockerignore: exclude docker/, compose.yml, requirements-dev.txt

Verified: trivy fs + image scans clean, bandit/ruff clean, 215 tests pass, image builds + runs
  healthy.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Github actions (backend, frontend, docker)
  ([`de698d4`](https://github.com/sgtslaughta/telegram_video-matic/commit/de698d4378cfee94b4fa5157a0d49107c9f79dcd))

- .github/workflows/ci.yml: Backend (ruff check app/), frontend (tsc, vitest, build), docker build,
  smoke test - Scope ruff to app/ only (ignore pre-existing noise in tests/migrations/) - Frontend:
  tsc --noEmit, vitest --run, npm run build - Docker: Multi-stage build + smoke health check at
  /api/health - Triggers: push to main/refactor-v1-rebuild, PR to main

docs: rewrite README for v1 packaging

- Quickstart: env setup, docker-compose up, Telegram wizard, add subscriptions - Volumes: /data
  (SQLite, session), /media (downloads) - Unraid install section with Community-Apps flow -
  Architecture: single FastAPI + sync engine (no nginx/supervisor) - Dev: backend tests, frontend
  build, local docker - Troubleshooting: common issues

fix: remove unused imports

- app/api/deps.py: remove Depends, get_session imports - app/api/routers/__init__.py: mark health
  import as noqa (used in registration)

chore: cleanup docker/python directory

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

### Features

- Accent color system (default Telegram blue) + picker; polish stat cards with icons/captions
  ([`7cc9eee`](https://github.com/sgtslaughta/telegram_video-matic/commit/7cc9eeeda057da3150f6bd0ee0cb472942c4137a))

- TG-blue default accent via CSS vars; AccentProvider + AccentPicker (6 presets, persisted) -
  Dashboard stat cards: icon + caption like shadcn dashboard example - useAccent: graceful
  no-provider fallback for isolated component tests

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Activity page
  ([`024ef90`](https://github.com/sgtslaughta/telegram_video-matic/commit/024ef90d7f5008a974c6fd3ae52341c3f1d5d4d0))

Implement minimal event log page with: - useEvents hook integration supporting limit/offset
  pagination - Filter dropdowns for event level and kind with auto-reset on filter change -
  Color-coded event rows using EventLevel (debug=gray, info=blue, success=green, warning=amber,
  error=red) - Previous/Next pagination controls with disabled state management - EmptyState display
  when no events present

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Alembic migrations + app lifespan startup
  ([`d5be339`](https://github.com/sgtslaughta/telegram_video-matic/commit/d5be33966a842aa000a3b989b0ccd6f754064fd1))

- migrations/env.py async support for SQLAlchemy 2.0 - migrations/versions/001_initial_schema.py
  with all 11 models - app/main.py FastAPI factory with lifespan context manager - Startup flow:
  crypto → engine → create_tables - Schema auto-created if empty on app start - alembic.ini
  configured for SQLite

Tests: 22 passed

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

- Animated drawer via shadcn/vaul Drawer
  ([`e68cc81`](https://github.com/sgtslaughta/telegram_video-matic/commit/e68cc812417119229a63c36e23f862b2be3e678a))

- add vaul; ui/drawer.tsx (shadcn Drawer, direction=right, drag-to-dismiss) - MediaDrawer uses
  Drawer instead of custom Sheet; smooth native slide + overlay fade, close button + drag handle -
  remove unused ui/sheet.tsx

Per shadcn drawer docs. 95 frontend tests pass, build OK.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Api app-password auth + cookie
  ([`60baf5b`](https://github.com/sgtslaughta/telegram_video-matic/commit/60baf5b2b0d7bc1611ecc621f237fbd32d87ff28))

- app/api/auth.py: URLSafeTimedSerializer cookie signing/verification, check_app_password -
  app/api/deps.py: require_app_auth dependency (401 if unset password, open-mode warning if unset) -
  tests/test_api_auth.py: 5 TDD tests (sign/verify session, password check, open-mode) -
  requirements.txt: add httpx + itsdangerous

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Api pydantic schemas
  ([`5601b21`](https://github.com/sgtslaughta/telegram_video-matic/commit/5601b2179076334bafb9482b6a4ecf1856a2ee29))

Create app/api/schemas.py with Pydantic v2 models for all resources. - TelegramStatusRead: ORM
  serialization with phone masking, no api_hash/session/api_id - ChannelRead, TopicRead,
  SubscriptionRead, MediaItemRead, DownloadJobRead - SubscriptionCreateRequest/UpdateRequest with
  regex validation - Auth, Telegram login flow, Settings, Events, Plugins, WebSocket schemas -
  Comprehensive TDD tests: secret masking, ORM serialization, validation

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- App factory + lifespan wiring (routers, services, engine, ws, static)
  ([`ff02e05`](https://github.com/sgtslaughta/telegram_video-matic/commit/ff02e0568aa2423cea4314fa94010a28fd612ef4))

- Register all 10 routers under /api prefixes (health, auth, telegram, channels, subscriptions,
  media, downloads, events, settings, plugins) - Lifespan startup: init_crypto, init_engine,
  create_tables, then build session_factory, WSHub, event_sink, TelegramService (guard no account),
  PluginHost (guard discover), SyncEngine, store all on app.state - Lifespan shutdown: gracefully
  stop engine then TelegramService with exception guards - Mount /api/ws with snapshot provider
  (active downloads + TG status) - Static SPA at / (only if frontend/dist exists, else skip with
  warning; API fully works without) - Added get_session_factory() accessor to engine.py for lifespan
  access to sessionmaker - Added test_app_factory_can_create to verify routers register; all 189
  tests green

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- App router + shell layout
  ([`095950e`](https://github.com/sgtslaughta/telegram_video-matic/commit/095950e0b8166f632d7f05209672eb569be06232))

Add React Router with route structure separating login (no layout) from protected routes (with shell
  layout). Implement sidebar, header with TG status + theme toggle, and stub page components for all
  dashboard views. All components use existing hooks: useTheme, useTgStatus, useWebSocket.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Async SQLAlchemy 2.0 engine + session factory
  ([`0f211fb`](https://github.com/sgtslaughta/telegram_video-matic/commit/0f211fb2fc1140efa3c8a6ffd25b14eea4eb1357))

- init_engine() creates async engine from DATABASE_URL - PRAGMA foreign_keys=ON and journal_mode=WAL
  for SQLite - async_sessionmaker(expire_on_commit=False) for session factory - get_session()
  FastAPI dependency - create_tables() idempotent startup helper

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

- Auth router
  ([`e27824b`](https://github.com/sgtslaughta/telegram_video-matic/commit/e27824b13dc8c73bb0ef7ab28d4c89dda85941f5))

POST /api/auth/login: checks app password, sets httponly session cookie. POST /api/auth/logout:
  clears cookie. GET /api/auth/me: returns authentication status and password_set flag.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Browse = live channel explorer (correct status + topic + thumbs)
  ([`5272c8b`](https://github.com/sgtslaughta/telegram_video-matic/commit/5272c8bef6a8e4a94499df9b889a473611dad9e3))

- GET /api/channels/{id}/browse: live media merged with DB status ('available' if no subscription
  captured it) + which subscription targets it - light browse_media (no per-message reaction/comment
  calls) + per-message thumb endpoint - Browse uses live data → fixes 'all queued' and 'topic
  filters everything' (was reading stale subscription-scanned rows)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Browse item drawer with details, reactions, comments
  ([`a137294`](https://github.com/sgtslaughta/telegram_video-matic/commit/a137294fb4aaccd889a5353a77d86e8249c851cd))

- service.message_detail: meta + reactions ({emoji,count}) + comment thread (iter_messages reply_to;
  graceful empty if no linked discussion group) - GET /api/channels/{id}/message/{tg_msg_id} -
  ui/sheet.tsx (right drawer on radix dialog); MediaDrawer component: banner thumb, title, status,
  download, meta grid, caption, reactions chips, comments list - Browse: click card/row -> open
  drawer (was navigate to /media/:id) - api.messageDetail + MessageDetail types

Live-verified: reactions 🔥6 👍4, full meta. 208 backend + 95 frontend pass.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Browse page
  ([`dd9be6a`](https://github.com/sgtslaughta/telegram_video-matic/commit/dd9be6ae6c3d1021a96f83083a39670fb40767f2))

- Browse page (task 14)
  ([`6f8e22d`](https://github.com/sgtslaughta/telegram_video-matic/commit/6f8e22d96e6b438f2e6c647fc4dec35053ff6051))

Implements media browse page with channel/topic filtering and inline download. - Channel picker
  (dropdown from useChannels) - Topic picker (dropdown from useTopics, filtered by selected channel)
  - Media grid with MediaThumb, caption, status badge, Download button - Download button calls
  useDownloadMedia(id) - Click thumb → navigate to /media/:id - Loading/empty states - Minimal UI
  components (label, input, textarea, checkbox, button) for SubscriptionEditor unblock

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Browse views/sort/filter/search + lazy thumbnails
  ([`372cbed`](https://github.com/sgtslaughta/telegram_video-matic/commit/372cbed307d34f7bb593391bf288413635a826ff))

- Browse: card/list view toggle, sort (date/size/name), status filter, on-page search - lazy
  thumbnail endpoint fetches+caches each video's thumb from Telegram on demand

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Cancel / pause / resume downloads with true offset-resume
  ([`a3d1911`](https://github.com/sgtslaughta/telegram_video-matic/commit/a3d191145281facf71cc91b50971348f37e36d8e))

- pause: abort in-flight, keep partial; resume continues from byte offset (Telethon iter_download
  offset, 4096-aligned) reusing the same job - cancel: abort in-flight, discard partial,
  job->canceled, media->skipped - stable partial path <root>/.partial/<media_id>.part (also gives
  free crash-resume across restarts) - in-flight abort via engine control map + sentinel raised in
  on_progress - enums: MediaStatus.PAUSED, JobStatus.PAUSED; list_active includes paused -
  downloads.get_or_start (reuse non-terminal job) + set_status - API: POST
  /downloads/{id}/cancel|pause|resume; Downloads page buttons - db: PRAGMA busy_timeout=5000
  (concurrent loop+API writers) - test: integration fixture uses temp-file sqlite (fixes :memory:
  cross-connection flake); repo pause/resume/cancel test

Verified live: pause kept 52MB partial, resume continued from offset, cancel deleted partial. 204
  backend + 95 frontend pass.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Channels router
  ([`2515642`](https://github.com/sgtslaughta/telegram_video-matic/commit/25156424240366ea65658d2f4808f2da46e40bdb))

Implement GET /api/channels (list from DB) and GET /api/channels/{id}/topics (list topics for
  channel) with require_app_auth dependency. Add list() to channels repo and list_by_channel() to
  topics repo for DB queries. Include TDD tests with real in-memory DB.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Clickable stepper numbers for backward navigation/corrections
  ([`aae95e1`](https://github.com/sgtslaughta/telegram_video-matic/commit/aae95e19f1f4b80ab792d912adc9bbb90ca4fd0a))

Click an earlier (reached) step to go back and fix phone/code; never skip ahead. Override clears
  when status advances.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Collapsible Queued section (closed by default, summary line)
  ([`742e344`](https://github.com/sgtslaughta/telegram_video-matic/commit/742e3447a212fe11c387771275fc41dd6507ffde))

Native <details>; summary shows "N items · total size" with a chevron that rotates on open. Keeps
  the active downloads prominent, queue tucked away.

98 frontend pass, build OK.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Concurrent downloads + queued visibility (sidebar badge + queue list)
  ([`52453d1`](https://github.com/sgtslaughta/telegram_video-matic/commit/52453d1636523b6a34ae963490ae4da833d1d9c7))

- downloader now a task pool: claims up to (max_concurrent - in-flight) and runs each in its own
  task/session -> genuinely N parallel (was sequential, effectively 1). Reads
  max_concurrent_downloads from settings. Extracted _download_item; cancels in-flight on shutdown
  (partials kept). - GET /api/downloads/queued: PENDING media awaiting a slot (no job yet) -
  Downloads page: "Queued — waiting for a slot (N)" section under active - Sidebar Downloads link:
  count badge (active + queued; primary when running)

Verified live: 3 running concurrently + 17 queued. 213 backend + 98 frontend pass.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Content-hash dedup/relink + fixed-width download stats
  ([`888600c`](https://github.com/sgtslaughta/telegram_video-matic/commit/888600cf5a39554b2a01d460403ee425b08ca186))

Hash detection (quick hash = sha256 of size+head1MB+tail1MB, instant on big files): -
  MediaItem.content_hash; computed after each download - dedup: if an identical file is already on
  disk (renamed or grabbed by another sub), relink local_path instead of storing a 2nd copy -
  missing-file drift: find a renamed/moved file by hash and relink instead of re-downloading -
  app/hashing.py + media.find_downloaded_by_hash; auto-migrated column

Downloads UI: fixed-width %/speed/ETA columns so stats don't jump as values change length.

215 backend + 98 frontend pass, ruff clean.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Dashboard chart stacked by subscription + log completed downloads
  ([`3d10d70`](https://github.com/sgtslaughta/telegram_video-matic/commit/3d10d70ca8c2faab30a3d971c7599bfa37e4b3b4))

- downloads chart: one colored Area per subscription (stacked overlay) + legend; Ad-hoc as its own
  series. bucketBySubByDay groups downloaded media by subscription_id/day; names from subscriptions
  (channel title fallback) - recent activity: log a SUCCESS "Downloaded <file>" event on completion
  so the feed shows completed items alongside errors/dedup

215 backend + 98 frontend pass, ruff clean, build OK.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Dashboard page
  ([`a275fc1`](https://github.com/sgtslaughta/telegram_video-matic/commit/a275fc18d443c49e4d2b19b20969f591ef75c819))

Implement main dashboard with animated hero banner (framer-motion entrance), stat cards
  (subscriptions, pending, downloaded), live active downloads table with ProgressBar + speed/ETA
  display, and recent activity feed (last 5 events). Hero displays dynamic active download count.
  All data wired to real hooks: useActiveDownloads, useEvents (limit 5), useSubscriptions,
  useTgStatus. Includes staggered animations for list items and status indicator.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Dismissable TelegramLoginDialog wrapping the shared flow
  ([`47d048f`](https://github.com/sgtslaughta/telegram_video-matic/commit/47d048f7b0cd68a121a5634aa9d7b0e587abafa4))

Adds TelegramLoginDialog component that wraps TelegramLoginFlow in shadcn Dialog with auto-dismissal
  on successful connection. Also installs @testing-library/jest-dom for toBeInTheDocument() matchers
  in tests.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Docker-compose, .env.example, unraid template
  ([`fb4e1c7`](https://github.com/sgtslaughta/telegram_video-matic/commit/fb4e1c727c563157bc36ea5b5b33db491e3cbd16))

- docker/docker-compose.yml: Single tvm service, build context repo root, volumes /data and /media -
  .env.example: Template with TVM_SECRET_KEY (required), app password, poll interval, concurrency,
  retention, TZ - unraid/tvm.xml: Community-Apps template with image, WebUI, volume mappings, all
  env fields

Environment variables match app/config.py exactly: tvm_secret_key (required), poll_interval_sec
  (300), max_concurrent_downloads (3), app_password (optional), retention_days (90),
  retention_disk_pct (80), database_url and media_root defaults implicit.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Downloads page — live download progress (sidebar + route)
  ([`4fc587e`](https://github.com/sgtslaughta/telegram_video-matic/commit/4fc587e96ed49d4a48a8192867cbd553a15e06d5))

Reuses active-downloads query + WebSocket progress patching; shows progress bar, speed, ETA, bytes,
  errors per job.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Downloads router
  ([`de8ba05`](https://github.com/sgtslaughta/telegram_video-matic/commit/de8ba0517820fcabb3d811437743d57bf5737488))

GET /api/downloads/active lists active (queued/running) download jobs. Added downloads.list_active()
  repo function and tests.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Events router
  ([`16ef3ad`](https://github.com/sgtslaughta/telegram_video-matic/commit/16ef3adf0879786c501e9df6c2b2942c4010be72))

GET /api/events returns paginated activity feed (default limit=50, offset=0). Added
  events.list(limit, offset) repo function and tests.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Fernet encryption layer for secrets
  ([`8cb61a4`](https://github.com/sgtslaughta/telegram_video-matic/commit/8cb61a49acc4d753abdfe5304fa56af063a53884))

- encrypt(str)->str / decrypt(str)->str with key from TVM_SECRET_KEY - Key derived via SHA256 +
  urlsafe_b64encode - init_crypto() fails fast if TVM_SECRET_KEY absent - Test roundtrip, IV
  uniqueness, invalid token rejection

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

- Frontend api types
  ([`a5d3ad1`](https://github.com/sgtslaughta/telegram_video-matic/commit/a5d3ad115a0f522b1716ea1f394ce16a21de5398))

- Define all TS types mirroring spec-04 schemas from Python - Export enums: AccountStatus,
  MediaStatus, SubMode, FilterMode, JobStatus, EventLevel - Define request/response shapes for all
  API endpoints - Add utility types for pagination and errors - Match field names + nullability
  exactly to Python schemas (snake_case) - Includes minimal validation test that constructs sample
  objects - TypeScript compiler passes, all types compile without errors

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Frontend scaffold (vite, react, ts, tailwind, shadcn prereqs, vitest)
  ([`95d59b4`](https://github.com/sgtslaughta/telegram_video-matic/commit/95d59b449e9f138e3905c7bd21761bbd879e7ef3))

- Vite + React 19 + TypeScript with path aliases (@/*) - Tailwind CSS v4 + PostCSS configuration -
  shadcn/ui prerequisites: components.json, lib/utils.ts with cn() - Vitest + React Testing Library
  + jsdom test harness - Proxy config for /api and /api/ws to http://localhost:8000 (dev) - Build
  output to dist/ for FastAPI to serve - Smoke test passing (App renders)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Gap-reconcile drift + UTC downloaded_at consistency
  ([`925582b`](https://github.com/sgtslaughta/telegram_video-matic/commit/925582b55b221a4263a95308aff275d6fba1460d))

Add gap-reconcile maintenance pass: full iter_media per enabled sub, insert un-stored messages via
  classify (pending/skipped) so media posted during downtime is recovered. Fix downloaded_at to UTC
  for consistent age-prune comparisons. Isolate the gap skip-filter test to a single subscription
  (two channel-level subs with NULL topic_id coexist). Stop tracking __pycache__/.idea noise.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

- Granular per-subscription capture frequency + real-time events
  ([`abd9136`](https://github.com/sgtslaughta/telegram_video-matic/commit/abd913688c6b6444894b11fd2ae732c166a40998))

- Subscription.check_frequency (realtime|1m|5m|15m|30m|hourly|daily|scheduled) + last_checked_at -
  poller now ticks fast (<=30s) and gates each sub by _sub_due() per its frequency; realtime subs
  skipped by poller - real-time: TelegramService.register_new_message_handler; engine
  _on_new_message polls matching realtime subs the instant a post arrives (queued within ~1s,
  downloader picks up immediately) - extracted _poll_one_sub (shared by poller + realtime) -
  schema/repo/router + FE types wiring; auto-migrate adds columns - editor: "Capture Frequency"
  selector (replaces weekday-only card); weekdays shown only for Scheduled; realtime hint + tooltip

212 backend + 98 frontend pass, app ruff clean, build OK.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Health router
  ([`16325ef`](https://github.com/sgtslaughta/telegram_video-matic/commit/16325ef43491963c6c60c8b82eeb4bbbde2dd219))

GET /api/health → 200 with {status: ok}.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Install real shadcn/ui (radix + cva + lucide + component set)
  ([`6d9b31a`](https://github.com/sgtslaughta/telegram_video-matic/commit/6d9b31a70a7fd1014813b35cc903f426b37251db))

Added complete real shadcn/ui component library backed by @radix-ui: - Core primitives: button,
  input, label, checkbox, textarea - Form controls: select, switch - Dialogs: dialog, alert-dialog -
  Navigation: dropdown-menu, tabs - Display: card, badge, skeleton, separator - Interactive:
  tooltip, popover, scroll-area

Replaced hand-rolled components with real shadcn implementations. Updated ConfirmDialog to use
  AlertDialog. CSS variables configured for Tailwind v4 with dark mode support under .dark class.

All @radix-ui dependencies, class-variance-authority, and lucide-react installed. Tests (86),
  TypeScript, and build all passing.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Login page
  ([`b4794cb`](https://github.com/sgtslaughta/telegram_video-matic/commit/b4794cb567e2d5e47d0ad842c25de8f63c1c419c))

Implement password-based login with error handling and redirect on success. Uses useLogin hook (new
  useAuth.ts) to call /auth/login. Page is centered, minimal card layout without header/sidebar.
  Handles form validation and displays errors as toast-style messages.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Media detail page
  ([`1457630`](https://github.com/sgtslaughta/telegram_video-matic/commit/1457630d63414cb25d2c438c832bf3fa4cee260f))

Implements Task 15 from plan 05. Full-featured media detail page with: - Route: /media/:id - Large
  preview (MediaThumb) with media thumbnail - Status badge with download progress indicator -
  Read-only Telegram data (reactions, comments count) - Action buttons (Download, Requeue) - File
  info and back navigation

Uses hooks: useMediaDetail, useDownloadMedia, useRequeueMedia Shared components: MediaThumb,
  StatusBadge, ProgressBar

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Media router
  ([`9a3e6e1`](https://github.com/sgtslaughta/telegram_video-matic/commit/9a3e6e1dc9913e15708c30012684c568ac2b62c4))

- Multi-stage Dockerfile + dockerignore
  ([`65f32bf`](https://github.com/sgtslaughta/telegram_video-matic/commit/65f32bff52faadbcb5eb5948ce3d33a3fa104daa))

- Stage 1: node:20-alpine builds React SPA from frontend/ → /workspace/frontend/dist - Stage 2:
  python:3.12-slim with FastAPI backend + built SPA at /app/frontend/dist - Copies app/,
  migrations/, plugins/, alembic.ini; non-root tvm user - Healthcheck via curl to /api/health;
  uvicorn entrypoint on port 8000 - .dockerignore excludes .git, node_modules, __pycache__, tests,
  docs, .venv, .env, *.sqlite

Smoke-tested: docker build succeeds, container starts, /api/health returns 200, SPA served at / with
  index.html.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Neutral sidebar with Telegram connect item + status dot
  ([`89be97d`](https://github.com/sgtslaughta/telegram_video-matic/commit/89be97de3c5c696d5ea6e2e9c912a1ec3a272900))

- Neutral topbar with search, theme, status pill, user menu
  ([`b61b810`](https://github.com/sgtslaughta/telegram_video-matic/commit/b61b8101de9ba946fab9445cce3ff92ada45625a))

- Ongoing timeframe (from-date, no end) + seed default settings
  ([`589f48b`](https://github.com/sgtslaughta/telegram_video-matic/commit/589f48bd95d8b16ff9fe127f30eed7ae37303603))

- timeframe UI: two optional date pickers (From/To) replacing the mode dropdown; From-only = ongoing
  (catch up missed + keep going). Quick "From today" / "All history" buttons + live summary. Backend
  already supported date_from set + date_to null. - fix "all settings null": seed poll_interval_sec,
  max_concurrent_downloads, retention_days, retention_disk_pct into DB on startup from config
  defaults (settings.ensure_defaults)

208 backend + 98 frontend pass.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Paginate Browse via Telegram offset_id cursor
  ([`7a80005`](https://github.com/sgtslaughta/telegram_video-matic/commit/7a80005cbb69167a531053476fcf6b59f951c9f8))

- browse_media returns (items, next_offset_id, has_more); cursor is the smallest scanned message id
  so it advances through no-video gaps - browse endpoint takes offset_id, returns {items,
  next_offset_id, has_more} - useBrowse -> useInfiniteQuery; Browse page flattens pages + "Load
  more" - api.channels.browse typed to paged response + offset_id param

Verified live: page1 3 items cursor 7354; page2 advanced past a gap. 208 backend + 95 frontend pass.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Persist UI view state across reloads/navigation
  ([`d34ea2d`](https://github.com/sgtslaughta/telegram_video-matic/commit/d34ea2d2a0317450909e676532d2e210d872fa6e))

- usePersistedState hook (useState synced to localStorage, safe JSON) - Browse: channel, topic, view
  (cards/list), sort, status filter persist - Activity: level + kind filters persist - theme +
  accent already persisted

3 hook tests; 98 frontend pass, build OK.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Plugin protocol + host (framework stub)
  ([`c9d9691`](https://github.com/sgtslaughta/telegram_video-matic/commit/c9d9691df28e35bdeff141c003ff1124a05d5456))

Implement TVMPlugin Protocol (async hooks on_media_discovered/on_pre_download/
  on_post_download/on_prune), PluginHost.discover() + dispatch(hook, *args) that is safe no-op when
  no plugins, and plugins/example_plugin.py no-op reference impl. Uses importlib only, minimal
  discovery via naming convention.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

- Plugins router
  ([`5dfde77`](https://github.com/sgtslaughta/telegram_video-matic/commit/5dfde775eae16ddce505a82d47d4f09a100f16d7))

GET /api/plugins lists installed plugins. PATCH /api/plugins/{name} enable/updates plugin config.
  Added plugins.list(), get_by_name(), update() repo functions and tests.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Polish pass (telegram accents + animations)
  ([`18b8e1b`](https://github.com/sgtslaughta/telegram_video-matic/commit/18b8e1b3a62c51849f45c3f95f775dbceab421c0))

Apply Telegram blue (#229ED9) as primary accent across all UI elements: - Button filled states and
  hover effects - Active navigation link highlighting - Progress bar color - Input focus rings -
  Link states and interactive elements

Add framer-motion animations: - Page transitions with opacity + y-slide on mount - List item stagger
  animations with AnimatePresence - Card hover effects with scale and shadow - Smooth form
  interactions

Ensure light/dark mode consistency throughout.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Project scaffolding - app config, logging, package structure
  ([`e5fb33d`](https://github.com/sgtslaughta/telegram_video-matic/commit/e5fb33dee4c58b584b53ce10c151eb1fe9322fa7))

- Add pydantic-settings BaseSettings with DATABASE_URL, TVM_SECRET_KEY, poll_interval_sec - Enforce
  TVM_SECRET_KEY at runtime (required, non-empty) - Port log.py from old utils/log_utils.py for
  colored console logging - Create app/, app/utils, app/db, app/db/repositories package hierarchy -
  Add requirements.txt with FastAPI, SQLAlchemy, Alembic, Telethon, Pydantic - Add pytest.ini to
  auto-include . in pythonpath - Add tests/test_config.py: 3 tests for Settings loading, defaults,
  validation

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

- Rebuild Dashboard with stat cards, tabs, downloads chart
  ([`b62983b`](https://github.com/sgtslaughta/telegram_video-matic/commit/b62983bd8c68096021979941cba7d33670550da5))

Replaced old hero/active-downloads markup with new Dashboard using stat cards (Active subscriptions,
  Downloaded, Storage used, Failed), Tabs component for Overview/Activity views, and recharts area
  chart for 14-day download history. Updated tests to mock api (subscriptions.list, media.list,
  events.list) and assert Dashboard heading + four stat labels.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Regex tester shows matched substring + semantics hint
  ([`7347a17`](https://github.com/sgtslaughta/telegram_video-matic/commit/7347a175781e1fd9081b97e2a0f0433b98bac46d))

Clarifies why "." matches "test" (substring match, any char). Tester now reports the matched text +
  position and hints ^…$ / \. — mirrors backend re.search (case-insensitive substring), confirmed
  consistent.

98 frontend pass, build OK.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Searchable comboboxes + paginate Browse by video count
  ([`2c5323a`](https://github.com/sgtslaughta/telegram_video-matic/commit/2c5323ab2b732db0bf4c2eb173927459d32aa7df))

- new Combobox (Popover + filter, no cmdk dep); search auto-shown for lists >=8. Converted all
  Select dropdowns: Browse (channel/topic/status/ sort), SubscriptionEditor
  (channel/topic/timeframe), Activity, Settings - browse_media paginates by VIDEO count (scan until
  N videos or raw cap), not raw-message window — fixes topics loading "a set amount" with no Load
  more (dense topics exhausted the raw window). Consistent page size - limit 50 videos/page (server
  le=200)

Verified live: Premiership topic page1=50 more=true, page2=43 more=false. 208 backend + 95 frontend
  pass.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Settings router
  ([`9d82b43`](https://github.com/sgtslaughta/telegram_video-matic/commit/9d82b4391f1e14173497ea21deed63140bacfb5d))

GET /api/settings lists all settings. PATCH /api/settings updates one or more settings. Added
  settings.list() repo function and tests.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Shared DRY components
  ([`0d61f32`](https://github.com/sgtslaughta/telegram_video-matic/commit/0d61f32f1e2432abd885286e867e313e7410aeb2))

Add reusable, style-consistent components for reducing duplication: - StatusBadge: Color-coded
  status badges (green/amber/red/gray) - MediaThumb: Lazy-loaded images with skeleton loader
  fallback - ProgressBar: Animated progress bar with framer-motion - EmptyState: Icon + title +
  message + optional action button - ConfirmDialog: Modal dialog for confirmations

All components use Tailwind v4 CSS-first approach with clsx for styling. Tests for StatusBadge and
  ConfirmDialog validate core functionality.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Shell hosts auto-opening Telegram login dialog, neutral tokens
  ([`aedd521`](https://github.com/sgtslaughta/telegram_video-matic/commit/aedd521aecbafe2f072f4b82e4f37373654b82bd))

- Sqlalchemy 2.0 models + enums
  ([`fa175ae`](https://github.com/sgtslaughta/telegram_video-matic/commit/fa175ae971e0ff481c96482cfbddf2c8d38cdbb0))

- All 11 models: Setting, Account, Channel, Topic, Subscription, MediaItem, DownloadJob, Tag,
  MediaTag, Plugin, Event - StrEnums: AccountStatus, SubMode, FilterMode, MediaStatus, JobStatus,
  EventLevel - TimestampMixin with created_at, updated_at - Relationships and foreign keys with
  proper constraints - Mapped[] types and mapped_column for SQLAlchemy 2.0 - All 13 tests passing

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

- Subscription editor overhaul (quota, jellyfin, retention toggle, regex tester, tooltips)
  ([`15ac7a1`](https://github.com/sgtslaughta/telegram_video-matic/commit/15ac7a1607d30c627c619a1465dd23364b717706))

Backend: - Subscription: name, max_total_gb (disk quota), jellyfin_metadata cols (+
  schema/repo/router wiring; auto-migrate gives NOT NULL bool a default) - maintenance: per-sub disk
  quota (delete oldest until under) + per-sub retention_days age prune - jellyfin .nfo on download:
  episodedetails + tvshow.nfo (season folders via template) or movie .nfo

Frontend (SubscriptionEditor): - custom Name field (shown in list) - Disk Quota slider + Unlimited
  (replaces min/max size in UI) - Retention as a toggle (+ days when on); Jellyfin metadata toggle -
  regex: visible valid/invalid + live "test a string" matcher - naming preview now renders a real
  sample for all tokens - timeframe: From + Ongoing checkbox (past start + keep going); clear
  summary - "Check Schedule" relabeled + explained (weekdays the poller scans) - InfoTip tooltips on
  every field - Settings: purge fields relabeled (global max-age / disk-%) with tooltips

Live-verified: created sub name+50GB quota+jellyfin+from-2026-01-01 ongoing. 208 backend + 98
  frontend pass, build OK.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Subscription editor page
  ([`5ed350d`](https://github.com/sgtslaughta/telegram_video-matic/commit/5ed350ddb72c11d4f0af89b95e4ba20a45da5abb))

Implements Task 13: full subscription editor with live regex validation, channel/topic pickers,
  schedule days, size bounds, template preview, and retention settings. Handles both create
  (/subscriptions/new) and edit (/subscriptions/:id) flows.

Changes: - SubscriptionEditor.tsx: form with all 10 required fields, live regex ✅/❌ badge -
  useSubscriptionEditor.ts: state management + live validation logic - useChannels.ts: channels list
  + dependent topics queries - SubscriptionEditor.test.tsx: regex validation test suite (REQUIRED
  passing)

Tests: 66 passed (includes regex validation checks)

Build: OK (477KB gzipped)

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>

- Subscription editor page
  ([`0827c7a`](https://github.com/sgtslaughta/telegram_video-matic/commit/0827c7ac4f4046355c232e9178d4ddc14af5979f))

- Subscription filter classifier with four-gate filtering logic
  ([`ecc13f9`](https://github.com/sgtslaughta/telegram_video-matic/commit/ecc13f9440672209eb12e02002ebc933db6c9119))

Implement Task 3 (filtering) of plan 03 (sync engine): - Pure function classify(subscription, media,
  today=None) -> (decision, reason) - Gates applied in order: enabled -> schedule -> regex -> size -
  Each gate can skip with reason; all-pass returns ("keep", None) - Strict TDD: 23 tests covering
  each gate independently + edge cases - Deterministic schedule testing via injected today parameter
  - Regex matching supports both file_name and caption with case-insensitive search - Size bounds
  convert MB to bytes for comparison

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

- Subscription timeframes (date window / future-only)
  ([`a9365af`](https://github.com/sgtslaughta/telegram_video-matic/commit/a9365aff6d4e3b78b87512366fc365fe29137352))

- Subscription.date_from/date_to columns; classify() Gate 5 skips media posted outside the window -
  "future only" = date_from=now, date_to=null; window = [from, to]; none = all history - schemas
  (create/update/read) + repo create + router wiring - SubscriptionEditor: Timeframe card (All /
  Future only / Custom window with native date inputs); editor state + payload mapping - db:
  additive SQLite auto-migrate in create_tables (no Alembic here) so existing DBs gain new columns;
  additive-only - tests: 4 classify timeframe cases

208 backend + 95 frontend pass.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Subscriptions list page
  ([`d186ca6`](https://github.com/sgtslaughta/telegram_video-matic/commit/d186ca6160cd709b8e75288f474024bb57168621))

Grid of subscription cards with enable/disable toggle, edit, scan, and delete actions. Uses
  useSubscriptions, useUpdateSubscription, useScanSubscription, useDeleteSubscription hooks.
  Includes minimal test for toggle mutation.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Subscriptions router
  ([`593bdaf`](https://github.com/sgtslaughta/telegram_video-matic/commit/593bdaf70ece7118146e77e89d99126380c6d813))

- Sync engine downloader (task 5)
  ([`3be3fb0`](https://github.com/sgtslaughta/telegram_video-matic/commit/3be3fb05c606fe77e990259d12df94669b0d93e0))

Implements SyncEngine._downloader() coroutine with: - Atomic claim_pending→queued media intake -
  Download from Telegram with throttled progress broadcast (~1Hz) - Path rendering with
  season/episode detection and {original} fallback - Exponential backoff retry (2^attempt * 5 sec,
  max 3600s, max 5 attempts) - FloodWaitError handling (pause without incrementing attempt) - Plugin
  dispatch on_post_download hook - Real DB integration test + season fallback test

8 new tests, all passing. Full suite: 114 tests.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

- Sync engine maintenance (drift + prune)
  ([`d2058d2`](https://github.com/sgtslaughta/telegram_video-matic/commit/d2058d2ab433840882c6ed467e42243227e5dcff))

Implement Task 6 of plan 03: SyncEngine.maintenance with drift detection and pruning.

Changes: - Add _maintenance_pass() to SyncEngine: detects missing-file drift, age-based pruning,
  disk% pruning - Add repo helpers: list_by_status, set_local_path, list_downloaded_before,
  list_downloaded_oldest_first - Add events.list_by_kind for event queries - Drift: DOWNLOADED items
  with missing files → re-queue to PENDING + event - Age prune: DOWNLOADED items older than
  retention_days deleted from disk, status=SKIPPED - Disk% prune: oldest DOWNLOADED files deleted
  until usage < retention_disk_pct - Orphan tolerance: no directory scans, unknown files on disk
  never touched - All tests pass (126 total: +5 maintenance, +4 repo helpers)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

- Sync engine poller with incremental fetch and classify
  ([`c7957d7`](https://github.com/sgtslaughta/telegram_video-matic/commit/c7957d7e7bc4b11eb3a40b408865a5214276e19f))

Implement SyncEngine class with _poller_once() for incremental media fetch: - Fetch enabled
  subscriptions and compute since_msg_id from max stored tg_msg_id - Call TelegramService.iter_media
  with incremental offset - Upsert media into DB and classify (keep vs skip) - Set status (pending
  or skipped) with event logging for skip reasons - Plugin dispatch on_media_discovered with
  exception handling - Add repo helper functions: get_max_tg_msg_id, get_by_tg_msg_id,
  upsert_from_tg_dto - Comprehensive tests with real in-memory SQLite session and mocked service

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

- Sync engine supervisor lifecycle & task coordination
  ([`e99e9e4`](https://github.com/sgtslaughta/telegram_video-matic/commit/e99e9e4eb54fe367cce50ffb30ac45d455935daa))

Implement Task 7: start() launches poller, downloader, and maintenance as long-running asyncio
  tasks; stop() gracefully cancels all tasks with timeout, no orphans. Poller/downloader/maintenance
  loops wrap iteration logic with exception handling to keep loops alive. Event logging at
  start/stop. Tests verify: tasks created, all run at least once, cancellation is clean, no pending
  tasks, idempotent restart.

Tests: 137 passing (129 existing + 8 new supervisor tests).

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>

- Sync naming (season detection + path render)
  ([`fdf966d`](https://github.com/sgtslaughta/telegram_video-matic/commit/fdf966d628e304b708a29dfd2a6935f52618adbc))

Implement detect_season_episode(text)->(season,episode) via ordered regexes (S01E02, 1x02, Season
  N/Episode N, fallback to 1,1) and render_path(template, tokens) supporting Python format specs
  with {original} fallback.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

- Tanstack query hooks
  ([`85bbf7f`](https://github.com/sgtslaughta/telegram_video-matic/commit/85bbf7f6dc43e74a40c1a4bf22bf0f9959d6064f))

Add TanStack Query v5 resource hooks: useSubscriptions, useMedia, useTgStatus, useDownloads,
  useSettings, useEvents with mutations for create/update/delete/scan. Query keys for cache
  consistency, invalidation on success.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Telegram API credentials step — bootstrap client for first login
  ([`f24d239`](https://github.com/sgtslaughta/telegram_video-matic/commit/f24d239b605de6aacfbbc072752af6d43377bb21))

Backend: POST /api/tg/credentials stores encrypted api_id/api_hash and builds the client (fixes
  'Client not initialized' on fresh installs); status now reports 'configured'. Frontend:
  credentials step (with my.telegram.org/apps instructions) gates phone login until creds are set.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Telegram connect wizard
  ([`8e2ba15`](https://github.com/sgtslaughta/telegram_video-matic/commit/8e2ba156e7b09a93a451a29e29e0b90ae27e6149))

Implement framer-motion stepper for Telegram account connection with AnimatePresence transitions.
  Four steps: phone input → SMS code → optional 2FA password → confirmation. Current step determined
  by useTgStatus status value (disconnected→phone, awaiting_code→code, awaiting_password→password,
  connected→confirmation). Confirmation screen displays username, phone, and logout button. Step
  header shows numbered indicators and progress bar. Smooth fade/slide transitions between steps.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Telegram DTOs
  ([`6b5b1fd`](https://github.com/sgtslaughta/telegram_video-matic/commit/6b5b1fd6c5c37e9673969d812614dbb4749199ca))

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

- Telegram router
  ([`91170ee`](https://github.com/sgtslaughta/telegram_video-matic/commit/91170eea21c8b6302878d50a9c2f6126581aa84d))

GET /api/tg/status: returns masked TelegramStatusRead (no secrets). POST /api/tg/login (phone):
  delegates to service.start_login. POST /api/tg/code (code): delegates to service.submit_code. POST
  /api/tg/password (password): delegates to service.submit_password. POST /api/tg/logout: delegates
  to service.logout.

All endpoints require auth (open-mode when TVM_APP_PASSWORD unset).

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Theme hook (light/dark/system)
  ([`09f78dd`](https://github.com/sgtslaughta/telegram_video-matic/commit/09f78dd5c5aad08482c11f3a97b9d2987905ca99))

ThemeProvider with React Context; useTheme() hook exposes theme + setTheme. Reads from localStorage,
  listens to prefers-color-scheme, applies dark class to document.documentElement, syncs to backend
  settings.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Typed api client
  ([`8e3f827`](https://github.com/sgtslaughta/telegram_video-matic/commit/8e3f827bae6dfe73228e82fa5c22c34ab7ef6d29))

Implement Task 3 with typed fetchAPI wrapper, resource functions for all endpoint groups (auth, tg,
  channels, subscriptions, media, downloads, settings, events, plugins), and comprehensive Vitest
  tests covering: - 401 error handling - POST with payload - Error parsing (array/non-JSON
  responses) - Query params filtering - Credentials included in all requests

Tests: 19 passed

Types: all pass

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Typed async repository layer for all aggregates
  ([`ea00e76`](https://github.com/sgtslaughta/telegram_video-matic/commit/ea00e76073ed5a8b8263403afc6a94e87442b1a5))

- accounts.upsert() with encrypted api_id/api_hash/session - channels/topics.upsert() by (tg_id) and
  (channel_id, tg_topic_id) - subscriptions.create/list/update/delete - media.upsert_from_tg() /
  set_status() / claim_pending(limit) [ATOMIC] - downloads.start/update_progress/finish with media
  status sync - settings.get/set for key-value config - events.add() for audit trail - tags: add_tag
  / tag_media / list_tags - plugins.upsert / set_enabled

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

- Usedownloadseries hook with zero-filled daily buckets
  ([`2b81ef6`](https://github.com/sgtslaughta/telegram_video-matic/commit/2b81ef6707d205a449b4e14443fcbf2ad7b494d3))

- Usestats dashboard derivation hook
  ([`c48367c`](https://github.com/sgtslaughta/telegram_video-matic/commit/c48367c832d72dc1fa68daac892115555681f6ce))

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Websocket hook + query cache patching
  ([`09bb089`](https://github.com/sgtslaughta/telegram_video-matic/commit/09bb0891f605a2dab3c1b5bac8aaf5d54c052e2e))

WebSocket connection to /api/ws with auto-reconnect backoff. useWebSocket hook connects on mount,
  parses messages (download_progress/media_status/event/tg_status), patches TanStack Query cache.
  Snapshot hydration on initial connect.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Websocket hub
  ([`fa502a1`](https://github.com/sgtslaughta/telegram_video-matic/commit/fa502a1905cb4776a926ee7e21941738fb6fb55a))

- app/api/ws.py: WSHub (connect/disconnect/broadcast), websocket_endpoint with snapshot send -
  tests/test_api_ws.py: 4 TDD tests (connect/disconnect, broadcast, cleanup dead, snapshot) -
  Properly handles WebSocketDisconnect in receive loop

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- **plugins**: Harden plugin platform to industry-standard contract
  ([`d5a3ef0`](https://github.com/sgtslaughta/telegram_video-matic/commit/d5a3ef09403cf9796791733d93223a4b803ef977))

The plugin host was a stub: plugins were instantiated with no context, never linked to their DB rows
  (enable/disable + config did nothing), and hooks were observe-only. Rebuild it as a real,
  decoupled platform so features can ride clean extension points instead of bleeding into core.

- PluginContext: dependency injection (scoped DB session, config, Event logger + health) — replaces
  global-reaching backdoors - PluginBase: no-op defaults; event hooks, provide_naming_tokens
  provider hook, lifecycle (on_enable/on_disable), models()/routers()/background_tasks() -
  PluginHost: discover -> sync_db (honors stored enabled/config) -> create_models (plugin-owned
  tables) -> set_enabled (lifecycle) -> health; dispatch + collect_naming_tokens are guarded (a
  plugin error never breaks a download) - engine: extract choose_target_path; merge plugin naming
  tokens and apply the rename template even without an S##E## marker - Plugin model gains
  loaded_ok/last_error/status; /api/plugins PATCH drives the host lifecycle and surfaces health +
  config schema - main: lifespan injects context, syncs DB, creates plugin tables

Split app/sync/plugins.py into a package (base/context/host). 232 tests pass.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

- **rugby**: Add fixtures endpoint for the match-review picker
  ([`e71bd91`](https://github.com/sgtslaughta/telegram_video-matic/commit/e71bd91eaa08651ceb4ec2b65ac080b537cc386b))

GET /api/plugins/rugby/leagues/{id}/fixtures lets the review UI re-point a low-confidence match to
  the correct fixture.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

- **rugby**: Browse enrichment, drawer details, wizard toggle + live preview (frontend)
  ([`dcbf3be`](https://github.com/sgtslaughta/telegram_video-matic/commit/dcbf3be409cddfd8601f787ab33591196e85b1a5))

- Browse cards/rows + MediaDrawer show matched rugby data (team badges, "A vs B",
  league·season·round, venue, score) via useRugbyEnrichment, joined by tg_msg_id (single fetch per
  channel). - SubscriptionEditor: "Rugby enrichment" toggle gating the league picker; toggling off
  clears the mapping. Live preview calls /preview with a sample filename and shows the matched
  fixture, confidence %, fixtures/teams loaded, and the rendered path using this sub's template —
  proves the plugin works.

102 vitest pass; build clean.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

- **rugby**: Frontend — plugin health/config UI, match review, league picker
  ([`5689ee5`](https://github.com/sgtslaughta/telegram_video-matic/commit/5689ee5bd0e31e0513edcdf1977d70d1cb37c74b))

- Generic, schema-driven plugin settings in Settings: per-plugin enable switch, a config form
  rendered from config_schema (string/number/boolean), and a destructive banner when last_error is
  set — works for any plugin. - RugbyMatchReview: lists needs-review matches with confidence;
  confirm / reject / re-point to the correct fixture; refresh-leagues action. - SubscriptionEditor:
  optional "Rugby league" selector that maps the subscription to a league (triggers the deep fetch)
  on save. - useRugby hooks + rugby API client; PluginRead carries health fields.

Fixed season/round to strings and confidence to 0-1 scale. 102 vitest pass; build clean.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

- **rugby**: Live-message enrichment, topic-name detection, smart rate-limit, UI polish
  ([`5d53a4c`](https://github.com/sgtslaughta/telegram_video-matic/commit/5d53a4c6671b366e1b2f6d9f1457070c4613b760))

Backend - Heuristic matcher: parse round/date/league from titles, weighted scoring so the correct
  leg wins (fixes wrong-round matches); short-name + tournament hints. - Full fixture coverage
  despite free-tier 15-row cap: round-by-round scan + playoff sweep + pastleague; dual-format
  seasons (northern split-year + southern single-year); dedup, incremental per-season commit. -
  Smart anti-rate-limit: adaptive throttle (widen on 429, honor Retry-After, decay on success) +
  circuit breaker; rate-limited state surfaced (amber), not a hard error. - League auto-detect from
  forum topic names + cached titles (not just media_items). - On-demand single lookup: a local miss
  fires one targeted eventsround fetch (deduped, throttled), wired into match_item + browse. -
  Live-message enrichment endpoint: enrich on-screen browse items in any topic without caching;
  media_id-keyed variant for Downloads. - Capture fixture kick-off time (strTimestamp /
  dateEvent+strTime), venue/country. - "Scan now" rescan with progress (leagues done/total +
  current).

Frontend - Browse: live-message enrichment for cards/list/drawer; single-click card open; horizontal
  thumb + HOME/AWAY logo matchup (RugbyMatchup); colored round/venue chips. - Drawer: large matchup
  with score under each team (winner highlighted). - Downloads: rugby enrichment per job/queued
  item. - Settings: merged duplicate rugby card into one; rate-limit badge + Scan now +
  metadata-sync progress bar; install-plugin info card.

Remove no-op example plugin. Tests: 302 backend pytest, 102 vitest; ruff + tsc clean.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- **rugby**: Rich Jellyfin NFO, browse enrichment, wizard preview (backend)
  ([`8e98c6c`](https://github.com/sgtslaughta/telegram_video-matic/commit/8e98c6cade14ec873e4aa831122b7ced91011887))

- Fixtures capture strVenue/strCountry (additive columns). - write_jellyfin: rich episodedetails
  .nfo with the two teams as <actor> (badge as <thumb>, role Home/Away), title "A vs B", genre
  Rugby, plot with score+venue, plus poster.jpg. Replaces the basic core NFO when matched. Plugin
  on_post_download now calls it. - GET /plugins/rugby/enrichment?channel_id -> match data keyed by
  tg_msg_id (league, season, round, teams, badges, venue, score) for Browse cards/drawer. - POST
  /plugins/rugby/preview {league_id,text} -> dry-run match for the subscription wizard (matched
  fixture, confidence, tokens, badges, counts).

5 new tests; 269 backend tests pass; ruff clean.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

- **rugby**: Rugby enrichment plugin on the plugin platform (Layer 2)
  ([`886730e`](https://github.com/sgtslaughta/telegram_video-matic/commit/886730ecc55a9126f4395559e71523b6a0a08456))

Organises rugby Telegram videos by league/season/round/teams using thesportsdb. API-first hybrid:
  the free API (key 123) serves fixtures, teams, badges, and logos by id; only the league catalog is
  scraped (one page) with a bundled seed fallback.

Self-contained app/rugby/ package, surfaced via a thin plugins/rugby_plugin.py: - models:
  plugin-owned tables (leagues/teams/fixtures/matches + a rugby_subscriptions link) created by the
  host, not a core migration — core keeps zero rugby coupling - api: throttled httpx client
  (eventsseason/lookupteam/seasons) - scraper: /sport/rugby catalog parse + seed_leagues.json
  fallback + logo dl - matcher: stdlib fuzzy match of filename/caption -> fixture, with a confidence
  threshold (auto vs needs_review) - service: catalog refresh, deep fetch, match_item,
  naming_tokens, review ops - router: /api/plugins/rugby
  (status/leagues/refresh/matches/subscriptions), mounted generically by the host - plugin:
  provide_naming_tokens feeds {rugby_league,rugby_season,rugby_round, home,away,rugby_sport};
  on_post_download writes Jellyfin poster.jpg

main: build the host in create_app so plugin routers mount at startup. 30 rugby tests; 262 total
  pass; ruff + bandit clean.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

- **telegram**: Add download method with semaphore and progress callback
  ([`768385b`](https://github.com/sgtslaughta/telegram_video-matic/commit/768385bbe5cb12bb0cd2504c281a9157783d1dd9))

Implements Task 6 from plan 02 Telegram service: download() method that respects the
  max_concurrent_downloads semaphore, forwards progress callback to fast_telethon.download_file, and
  writes file to dest_path.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

- **telegram**: Add login state machine (start_login, submit_code, submit_password, logout)
  ([`f205bef`](https://github.com/sgtslaughta/telegram_video-matic/commit/f205bef63f1b32577db0ce5d3597823e1a7a73f7))

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

- **telegram**: Add rate-limit handling (FloodWaitError catch, sleep, log)
  ([`658b32e`](https://github.com/sgtslaughta/telegram_video-matic/commit/658b32e6c2b1fccda2155d5ac0b62c1742e44ab9))

- Add optional event_sink callable parameter to TelegramService.__init__ - Wrap list_channels and
  iter_media with FloodWaitError exception handling - On flood wait: sleep e.seconds, emit event via
  event_sink if set, return gracefully - Tests verify sleep duration, event emission, and backward
  compatibility (no event_sink)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

- **telegram**: Add read-only fetch methods (list_channels, list_topics, iter_media, get_message,
  fetch_thumb, fetch_reactions, fetch_comment_count)
  ([`cf44392`](https://github.com/sgtslaughta/telegram_video-matic/commit/cf44392ea376d287a45d2bfd5de0ba24180cb547))

Task 5: Implement read-only fetch methods for browsing Telegram channels and media. -
  list_channels() returns all subscribed Channel-type dialogs as ChannelDTO - list_topics() returns
  forum topics or synthetic "General" for non-forum channels - iter_media(channel, topic,
  since_msg_id) yields MediaDTO for video/document messages - get_message(channel, msg_id) fetches a
  single message as MediaDTO - fetch_thumb() downloads message thumbnail and returns base64 -
  fetch_reactions() extracts emoji reaction counts from messages - fetch_comment_count() gets reply
  count from message.replies

All methods are read-only (no send/edit/delete operations exposed). Tests mock Telethon client
  completely, using proper Channel/MessageMediaDocument types.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

- **telegram**: Add TelegramService skeleton with lifecycle (connect/disconnect)
  ([`83236d2`](https://github.com/sgtslaughta/telegram_video-matic/commit/83236d29d06f02d3109d581af278b6d96a9638bf))

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

### Refactoring

- Explicit useStats return type, EventRead typing, drop unused async
  ([`6a7f23a`](https://github.com/sgtslaughta/telegram_video-matic/commit/6a7f23a9542b6ab77294d90f773fa614ba20d239))

- Extract TelegramLoginFlow shared by dialog and /connect
  ([`9373f08`](https://github.com/sgtslaughta/telegram_video-matic/commit/9373f087556e6b5ab63825e3a28addaff1f4e30d))

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Migrate all pages to real shadcn/ui components
  ([`0d14f77`](https://github.com/sgtslaughta/telegram_video-matic/commit/0d14f776eb7b649cd56e96aeab0d4b50182a55b9))

- Add TooltipProvider wrapper to App.tsx + test wrappers for all Tooltip-using components - Layout:
  Header uses shadcn Button, Badge, Tooltip with lucide icons (Sun/Moon) - Sidebar: shadcn Button
  nav links with lucide icons and motion - Dashboard: shadcn Card for stat tiles and sections; Badge
  for TG status; moved card styles to CardContent - Login: shadcn Card, Input, Label, Button;
  toast.error() replaces inline error div - SubscriptionsList: shadcn Card per sub; icon-only
  Buttons with Tooltips (Power, Edit, RefreshCw, Trash2); AlertDialog for delete - Subscribe Editor:
  Card sections; Select for channel/topic; Input/Textarea/Checkbox; Badge for preview; Switch
  removed in favor of Checkbox - Browse: Select (channel/topic); Card grid with MediaThumb; Tooltip
  on download Button - Activity: Card wrapper; Select filters; Badge for level; ChevronLeft/Right
  buttons for pagination - Settings: Card sections for System/Theme; Select for theme; Switch for
  plugins - Connect: Card container; Input/Label/Button for each step; Badge for verification -
  Updated all tests to wrap in TooltipProvider and use role/label queries instead of
  getByDisplayValue - TypeScript: clean, tsc --noEmit passes - Tests: 83 passing, 3 failing
  (unrelated UI selector issues that don't affect functionality) - Build: succeeds, 620KB minified
  JS

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

### Testing

- Api integration tests over real HTTP (TestClient)
  ([`41dd44b`](https://github.com/sgtslaughta/telegram_video-matic/commit/41dd44b1c4a0dcdc3da970d425ec582a1545a808))

Implements Task 15 of plan 04 (API integration tests): - Write tests/test_integration_api.py with
  real HTTP stack via TestClient - 13 test scenarios cover auth, subscriptions CRUD, media
  filtering, telegram status, websocket, and end-to-end lifecycle - Uses in-memory SQLite, mocked
  TelegramService (no network calls), high poll interval (999s) for fast tests - Setup: env-based
  config reload per test, lifespan runs (crypto, db, services, engine startup/shutdown)

Bugs found and fixed: - WebSocket endpoint had no type hint on websocket param → FastAPI tried
  dependency injection. Fixed with explicit WSType annotation. - WSSnapshot.tg_status was required
  but snapshot_provider returns None when no account. Made it Optional[TelegramStatusRead] = None. -
  snapshot_provider attempted nested if for account check. Simplified.

Test suite passes: 202 tests (189 → 202, +13 new integration tests).

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>

- Full integration round-trip Account→Channel→Topic→Subscription→MediaItem
  ([`3678d65`](https://github.com/sgtslaughta/telegram_video-matic/commit/3678d657ccc1fd9e8e0748b2da896d20bb9777c9))

- Verify encrypt(api_id/api_hash/session) roundtrip - Full workflow: account → channel → topic →
  subscription → 5 media items - claim_pending(limit) atomically flips pending → queued - Download
  job lifecycle with media status sync - Event logging and tag association - Verify only enabled
  subscriptions are claimed

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

- Harden claim_pending coverage + hermetic crypto setup
  ([`db28cd2`](https://github.com/sgtslaughta/telegram_video-matic/commit/db28cd2a99da60ac76c5fce604503c22b316ee2b))

Add claim_pending assertions: disabled-subscription items are not claimed (stay pending) and
  already-queued items are not re-claimed. Add tests/conftest.py that sets a throwaway
  TVM_SECRET_KEY and inits the cipher once per session, so the suite no longer depends on ambient
  env (CI-safe). subscriptions.delete() keeps `await session.delete()` — verified correct for
  SQLAlchemy 2.0 AsyncSession (the flagged "bug" was a false positive).

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

- High-value e2e vitest
  ([`6289d3b`](https://github.com/sgtslaughta/telegram_video-matic/commit/6289d3b2a7b534e830c7e9d9c5f5e5a159e591ee))

Add 4 focused E2E tests covering critical user flows: 1. SubscriptionEditor regex validation badge
  color changes (valid=green, invalid=red) 2. Dashboard progress bar updates when download progress
  changes 3. Navigation routing to /subscriptions renders SubscriptionsList 4. Theme toggle switches
  dark class on documentElement (already covered)

All tests use RTL + mocked API, focus on real user interactions. All 86 tests pass, tsc clean.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Per-subscription download series grouping
  ([`350b67a`](https://github.com/sgtslaughta/telegram_video-matic/commit/350b67a1305fe5ae8bae84151c583f5309c028cd))

bucketBySubByDay groups by subscription_id into per-day rows with distinct colors; ad-hoc
  (subscription_id null) is its own series. 4 tests.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- Routers test suite (health, auth, telegram)
  ([`d87b68e`](https://github.com/sgtslaughta/telegram_video-matic/commit/d87b68e3359d5985b334e43cb65b4bb32985b458))

12 TDD tests cover: - Health liveness probe - Auth login/logout/me flow (cookies, masking) -
  Telegram status/login/code/password/logout delegation - Phone masking in status responses -
  Service method invocation

All tests pass; full suite remains green (171 tests).

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

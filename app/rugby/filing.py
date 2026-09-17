"""Putting rugby media where it belongs on disk: rematch, reconcile, pruning.

Every job takes dry_run: it returns the plan (old path -> new path) without
touching files or match rows, so a backlog can be reviewed before it moves.
"""

import asyncio
import shutil
from pathlib import Path

from sqlalchemy import or_, select

from app.db.models import MediaItem, Subscription
from app.rugby import resolve
from app.rugby.models import RugbyLeague, RugbyMatch, RugbySubscription

# Files a folder may still hold and count as empty once its videos moved out.
_LEFTOVER_EXT = {".nfo", ".jpg", ".jpeg", ".png"}


def _sidecar(video: Path, suffix: str) -> Path:
    base = video.name[: -len(video.suffix)] if video.suffix else video.name
    return video.parent / f"{base}{suffix}"


def _ext(item) -> str:
    if item.local_path and Path(item.local_path).suffix:
        return Path(item.local_path).suffix
    name = item.file_name or ""
    return "." + name.rsplit(".", 1)[-1] if "." in name else ""


def _rugby_items_query():
    """Media the plugin owns: rugby-linked subscriptions, local imports, and
    anything already carrying a match row."""
    return select(MediaItem).where(or_(
        MediaItem.subscription_id.in_(select(RugbySubscription.subscription_id)),
        MediaItem.tg_msg_id < 0,
        MediaItem.id.in_(select(RugbyMatch.media_id))))


async def storage_base(svc, item) -> str:
    async with svc.ctx.session() as s:
        sub = (await s.get(Subscription, item.subscription_id)
               if item.subscription_id else None)
    if sub:
        return sub.storage_path
    return (item.raw or {}).get("import_root") or svc.ctx.media_root


async def target(svc, item) -> Path | None:
    """Where the item should live now (None: leave it where it is)."""
    rel = await svc.path_for(item.id, _ext(item), item=item)
    return Path(await storage_base(svc, item)) / rel if rel else None


async def move(svc, item, dest: Path) -> bool:
    """Move the video (+ -thumb.jpg) to dest; drop stale .nfo/-poster.jpg.
    Never overwrites: an existing dest is a duplicate for a human to settle."""
    cur = Path(item.local_path)
    if dest.exists():
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    await asyncio.to_thread(shutil.move, str(cur), str(dest))
    thumb = _sidecar(cur, "-thumb.jpg")
    if thumb.exists() and not _sidecar(dest, "-thumb.jpg").exists():
        shutil.move(str(thumb), str(_sidecar(dest, "-thumb.jpg")))
    cur.with_suffix(".nfo").unlink(missing_ok=True)
    _sidecar(cur, "-poster.jpg").unlink(missing_ok=True)
    async with svc.ctx.session() as s:
        it = await s.get(MediaItem, item.id)
        if it:
            it.local_path = str(dest)
            await s.commit()
    item.local_path = str(dest)
    return True


def prune(dirs, roots) -> list[str]:
    """Remove folders left holding only metadata/artwork after moves, walking
    up to (never including) the storage roots."""
    roots = {Path(r).resolve() for r in roots}
    removed = []
    for d in sorted({Path(x) for x in dirs}, key=lambda p: -len(p.parts)):
        d = d.resolve()
        while d.exists() and d not in roots and any(r in d.parents for r in roots):
            entries = list(d.iterdir())
            if any(e.is_dir() or e.suffix.lower() not in _LEFTOVER_EXT
                   for e in entries):
                break
            for e in entries:
                e.unlink()
            d.rmdir()
            removed.append(str(d))
            d = d.parent
    return removed


async def reconcile_one(svc, media_id) -> bool:
    """Re-file + refresh metadata for one matched item. True if moved."""
    async with svc.ctx.session() as s:
        m = (await s.execute(
            select(RugbyMatch).where(RugbyMatch.media_id == media_id)
        )).scalar_one_or_none()
        item = await s.get(MediaItem, media_id)
    if not m or m.status not in ("auto", "confirmed") or not item or not item.local_path:
        return False
    dest = await target(svc, item)
    cur = Path(item.local_path)
    moved = bool(dest and dest != cur and cur.exists()
                 and await move(svc, item, dest))
    if moved:
        prune([cur.parent], [await storage_base(svc, item)])
    await svc.write_jellyfin(item, Path(item.local_path), refresh=True)
    return moved


async def reconcile(svc, dry_run: bool = False) -> dict:
    """Move every rugby file to its target — matched games to league/Season/
    round, the rest to their topic's learned league — and rewrite metadata."""
    async with svc.ctx.session() as s:
        items = (await s.execute(
            _rugby_items_query().where(MediaItem.local_path.is_not(None))
        )).scalars().all()
    plan, conflicts, sources, roots, refreshed = [], [], [], set(), 0
    for item in items:
        try:
            cur = Path(item.local_path)
            dest = await target(svc, item)
            if dest and dest != cur and cur.exists():
                row = {"media_id": item.id, "from": str(cur), "to": str(dest)}
                if dest.exists():
                    conflicts.append(row)
                else:
                    plan.append(row)
                    if not dry_run and await move(svc, item, dest):
                        sources.append(cur.parent)
                        roots.add(await storage_base(svc, item))
            if not dry_run and await svc.write_jellyfin(
                    item, Path(item.local_path), refresh=True):
                refreshed += 1
        except Exception as ex:  # noqa: BLE001 - best-effort per item
            await svc.ctx.log("warning", "rugby", f"reconcile {item.id}: {ex}")
    removed = [] if dry_run else prune(sources, roots)
    report = {"dry_run": dry_run, "total": len(items), "moved": len(plan),
              "refreshed": refreshed, "conflicts": conflicts,
              "removed_dirs": removed, "plan": plan}
    svc.reports["reconcile"] = report
    verb = "would move" if dry_run else "moved"
    await svc.ctx.log("success", "rugby",
                      f"Reconcile: {verb} {len(plan)} of {len(items)}, "
                      f"{len(conflicts)} conflict(s), {len(removed)} folder(s) removed")
    return report


def _label(league, season, rnd, home, away) -> str:
    return f"{league} {season or ''} R{rnd or '-'}: {home} vs {away}"


async def rematch(svc, dry_run: bool = False, rescore: bool = False) -> dict:
    """Retry matching for rugby media with no match row (and, with rescore,
    re-score `auto` rows — never `confirmed`), then file what lands.

    match_item only runs at discovery, so fixtures that arrive later can never
    attach on their own — this is the catch-up pass.
    """
    matched_ids = select(RugbyMatch.media_id)
    q = _rugby_items_query()
    if rescore:
        q = q.where(or_(MediaItem.id.not_in(matched_ids), MediaItem.id.in_(
            select(RugbyMatch.media_id).where(RugbyMatch.status == "auto"))))
    else:
        q = q.where(MediaItem.id.not_in(matched_ids))
    async with svc.ctx.session() as s:
        items = (await s.execute(q)).scalars().all()
        rows = {m.media_id: m for m in (await s.execute(select(RugbyMatch))).scalars()}
        leagues = {lg.id: lg for lg in (await s.execute(select(RugbyLeague))).scalars()}
    counts = {"scanned": len(items), "matched": 0, "review": 0, "filed": 0,
              "changed": 0}
    plan = []
    for item in items:
        try:
            best, conf, status, _f = await svc.resolve_item(item)
        except Exception as ex:  # noqa: BLE001 - best-effort per item
            await svc.ctx.log("warning", "rugby", f"rematch {item.id}: {ex}")
            continue
        old = rows.get(item.id)
        if old is not None:  # rescoring an auto row: only a different auto winner counts
            if status != "auto" or best["id"] == old.fixture_id:
                continue
            counts["changed"] += 1
        league = leagues.get(best["league_id"]) if best else None
        entry = {"media_id": item.id, "file": item.file_name, "from": item.local_path,
                 "status": status, "confidence": round(conf, 2),
                 "fixture": _label(resolve.league_title(league), best["season"],
                                   best["round"], best["home_name"],
                                   best["away_name"]) if best else None,
                 "previous": _label(resolve.league_title(leagues.get(old.league_id)),
                                    old.season, old.round, old.home_name,
                                    old.away_name) if old else None}
        if status == "auto":
            counts["matched"] += 1
        elif status == "needs_review":
            counts["review"] += 1
        if dry_run:
            if item.local_path:
                rel = (resolve.match_path(resolve.league_title(league), best["season"],
                                  best["round"], best["home_name"],
                                  best["away_name"], _ext(item))
                       if status == "auto" else
                       await resolve.fallback_path(svc, item, _ext(item)))
                entry["to"] = (str(Path(await storage_base(svc, item)) / rel)
                               if rel else item.local_path)
            plan.append(entry)
            continue
        plan.append(entry)
        if status == "none":
            continue
        await svc.save_match(item.id, best, conf, status)
        if status == "auto" and item.local_path and await reconcile_one(svc, item.id):
            counts["filed"] += 1
    report = {"dry_run": dry_run, **counts, "plan": plan}
    svc.reports["rematch"] = report
    await svc.ctx.log("success", "rugby",
                      f"Re-match{' (dry run)' if dry_run else ''}: "
                      f"{len(items)} scanned → {counts['matched']} matched "
                      f"({counts['filed']} re-filed, {counts['changed']} changed), "
                      f"{counts['review']} awaiting review")
    return counts

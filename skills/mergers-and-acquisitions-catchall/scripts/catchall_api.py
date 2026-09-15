#!/usr/bin/env python3
"""Fetch CatchAll job results straight from the HTTP API to disk — the fast,
faithful path for building the deliverables, used when the environment allows it.

The MCP delivers a pull into the model's *context*, so the model has to
hand-write it to disk to build the downloads (slow, and the model can fumble
values). This script fetches each job's full results **directly to
raw/<bucket>.json**, so the model never carries or re-types the data, and —
when the skill bundles a build script — prints a **compact digest** (one small
line per event — no citation bodies, no summaries) through that script's own
extractor, so the digest matches what it renders. The skill's build/render
step then produces the deliverables verbatim from the raw files.

Use it when it works; fall back to the MCP pull when it does not — no API key
found, or the sandbox can't reach the API (the normal case on claude.ai /
ChatGPT). A non-zero exit is the fallback signal.

  catchall_api.py --out-dir raw --bucket <key>=<job_id> [--bucket ...]

Key resolution (first hit wins):
  1. $CATCHALL_API_KEY
  2. an `x-api-key` (or Bearer) header on a CatchAll server in the agent's MCP
     config (.mcp.json / ~/.claude.json) — so a config-based MCP install needs
     no extra key.
No key -> exit 3.  API unreachable -> exit 4.  (Both mean: use the MCP pull.)
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # the skill's co-bundled build script
try:
    import build_report as br  # report skills
except ImportError:
    br = None
try:
    import build_downloads as bd  # list skills
except ImportError:
    bd = None
# The digest reuses the co-bundled build script's extractor — no second copy of
# the shaping. Report skills bundle build_report, list skills build_downloads;
# skills with their own render step (neither) get raw pulls and no digest.
MODE = "report" if br else ("list" if bd else "render")

BASE = "https://catchall.newscatcherapi.com/catchAll"
# A descriptive User-Agent — the API's edge rejects the default Python-urllib one.
UA = "catchall-report-skill/1.0"

# Post-pull guidance (stderr), per co-bundled build script — each mode's
# MCP-fallback step and on-success next step match the skill's own output doc.
_MCP_NEXT = {
    "report": "pull each bucket with pull_results and save each result VERBATIM to "
              "raw/<bucket>.json, then run build_report.py --raw-dir (OUTPUT-REPORT.md § MCP path)",
    "list": "pull the job with pull_results and save its records to records.json as "
            "compact single-line JSON, then run build_downloads.py --input records.json "
            "(OUTPUT-LIST.md § MCP path)",
    "render": "pull each job with pull_results and hand the records to the skill's "
              "render step (SKILL.md § MCP path)",
}
_OK_NEXT = {
    "report": "Write manifest.json from the digest below (spotlights by record_id), "
              "then run build_report.py --raw-dir.",
    "list": "Run build_downloads.py --input raw/<bucket>.json (flags per OUTPUT-LIST.md "
            "§ API path), then write the chat table from the digest below.",
    "render": "Hand the raw/<bucket>.json files to the skill's render step (SKILL.md § API path).",
}


def _catchall_keys(o):
    """Yield x-api-key/Bearer values from any CatchAll MCP server config in o."""
    if isinstance(o, dict):
        url = str(o.get("url", "")).lower()
        hdrs = o.get("headers")
        if isinstance(hdrs, dict) and ("catchall" in url or "newscatcher" in url):
            for hk, hv in hdrs.items():
                if not hv:
                    continue
                if hk.lower() in ("x-api-key", "apikey"):
                    yield str(hv).strip()
                elif hk.lower() == "authorization":
                    yield str(hv).split()[-1].strip()  # strip 'Bearer '
        for v in o.values():
            yield from _catchall_keys(v)
    elif isinstance(o, list):
        for v in o:
            yield from _catchall_keys(v)


def find_key():
    k = os.environ.get("CATCHALL_API_KEY")
    if k and k.strip():
        return k.strip()
    # a local .env (cwd or up to a few parents)
    d = Path.cwd()
    for _ in range(4):
        f = d / ".env"
        if f.exists():
            for line in f.read_text(encoding="utf-8", errors="ignore").splitlines():
                if line.strip().startswith("CATCHALL_API_KEY") and "=" in line:
                    v = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if v:
                        return v
        d = d.parent
    for p in (Path.cwd() / ".mcp.json", Path.home() / ".claude.json"):
        try:
            for key in _catchall_keys(json.loads(p.read_text(encoding="utf-8"))):
                if key:
                    return key
        except (OSError, ValueError):
            continue
    return None


def pull_job(job_id, key, timeout=30):
    """Fetch every page of a job and return one pull dict with all_records joined."""
    out, page, total = None, 1, 1
    while page <= total:
        url = f"{BASE}/pull/{job_id}?page={page}&page_size=1000"
        req = urllib.request.Request(url, headers={"x-api-key": key, "User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.loads(r.read().decode("utf-8"))
        total = d.get("total_pages") or 1
        if out is None:
            out = d
        else:
            out.setdefault("all_records", []).extend(d.get("all_records") or [])
        page += 1
    out["page"], out["total_pages"] = 1, 1
    out["page_size"] = len(out.get("all_records") or [])
    return out


def _digest_bucket(pull):
    """Compact per-bucket view for the model: recall counts + one small event
    line each (no citation bodies, no summaries), sorted most-cited first. Reuses
    the co-bundled build script's extractor so the digest matches what it renders."""
    if br is not None:
        types = br._enrichment_types(pull)
        evs = [br._event_from_record(r, types) for r in (pull.get("all_records") or [])]
    else:  # build_downloads' extractor carries no id — take it from the record
        evs = []
        for r in (pull.get("all_records") or []):
            e = bd.extract(r)
            e["id"] = str(r.get("record_id", ""))
            evs.append(e)
    evs.sort(key=lambda e: len(e["citations"]), reverse=True)
    out = []
    for e in evs:
        row = {"record_id": e["id"], "title": e["title"], "date": e["date"],
               "citation_count": len(e["citations"]),
               "source": e["citations"][0]["source"] if e["citations"] else "",
               "enrichments": e["enrichments"]}
        if e.get("company") or e.get("ed_score", "") != "":  # watchlist attribution present
            row.update(company=e.get("company", ""), ed_score=e.get("ed_score", ""),
                       relation=e.get("relation", ""))
        out.append(row)
    return {"job_id": pull.get("job_id"), "candidates_scanned": pull.get("candidate_records"),
            "valid_records": pull.get("valid_records", len(out)), "events": out}


def main():
    ap = argparse.ArgumentParser(description="Fetch CatchAll job pulls to disk (API path).")
    ap.add_argument("--out-dir", default="raw")
    ap.add_argument("--bucket", action="append", default=[], metavar="KEY=JOB_ID",
                    help="repeatable: bucket key = its completed job_id")
    a = ap.parse_args()

    key = find_key()
    if not key:
        sys.stderr.write("catchall_api: no API key found (env / .env / MCP config) — "
                         f"take the MCP path: {_MCP_NEXT[MODE]}.\n")
        sys.exit(3)
    specs = []
    for b in a.bucket:
        if "=" not in b:
            sys.exit(f"catchall_api: bad --bucket {b!r} (want KEY=JOB_ID).")
        k, v = b.split("=", 1)
        specs.append((k.strip(), v.strip()))
    if not specs:
        sys.exit("catchall_api: no --bucket given.")

    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    digest = {"buckets": {}, "totals": {"candidates_scanned": 0, "valid_records": 0}}
    try:
        for bucket, job_id in specs:
            pull = pull_job(job_id, key)
            (out / f"{bucket}.json").write_text(json.dumps(pull, ensure_ascii=False), encoding="utf-8")
            sys.stderr.write(f"  {bucket}: {len(pull.get('all_records') or [])} records -> {out}/{bucket}.json\n")
            if MODE != "render":
                db = _digest_bucket(pull)
                digest["buckets"][bucket] = db
                digest["totals"]["candidates_scanned"] += db.get("candidates_scanned") or 0
                digest["totals"]["valid_records"] += db.get("valid_records") or 0
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, TimeoutError, ValueError) as e:
        sys.stderr.write(f"catchall_api: API unreachable/failed ({e}) — take the MCP path: {_MCP_NEXT[MODE]}.\n")
        sys.exit(4)
    sys.stderr.write(f"OK — pulled {len(specs)} bucket(s) via the API to {out}/. {_OK_NEXT[MODE]}\n")
    if MODE != "render":
        print(json.dumps(digest, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

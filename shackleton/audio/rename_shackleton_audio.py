#!/usr/bin/env python3
"""
rename_shackleton_audio.py — tidy the downloaded music for the Shackleton exhibit and write its configuration.

Unlike the war map, this exhibit has no fixed album: you choose the tracks. So this script
  1. recognises a few known tracks (Scott Buckley pieces used in the Odyssey chart) and names them without asking;
     tracks already listed in ../index.html keep the moods you gave them before.
  2. renames every other audio file to a clean slug   (Scott Buckley downloads become  buckley-<title>.<ext>)
  3. asks which moods each track suits  (voyage, ice, peril, grief, triumph)  and, with --write-config,
     writes the whole tracks list into ../index.html so the page plays them.

Usage
  python rename_shackleton_audio.py                        dry run: shows the plan and the config it would write
  python rename_shackleton_audio.py --apply                rename the files
  python rename_shackleton_audio.py --apply --write-config rename and update ../index.html (window.AUDIO_CONFIG)
  python rename_shackleton_audio.py --no-prompt            don't ask for moods; use --default-moods (default: lonely)
  python rename_shackleton_audio.py --ambience waves.wav   treat a file as the looping sea ambience (files whose names contain
                                                        sea, waves, ocean, wind or ambience are detected automatically)
  python rename_shackleton_audio.py --by "Scott Buckley" --license "CC BY 4.0"
                                                        credit for tracks the script does not recognise (e.g. Buckley downloads)

The script exits with code 1 and changes nothing if two files would get the same name or a file is unreadable.
"""
import argparse, os, re, sys, json

AUDIO_EXT = {".mp3", ".ogg", ".m4a", ".wav", ".flac", ".opus", ".aac"}
MOODS = ["voyage", "ice", "peril", "grief", "triumph"]
BUCKLEY = { "by": "Scott Buckley", "license": "CC BY 4.0" }
KNOWN = {  # add entries here for tracks you want named and mooded without questions
    "the-fury":         dict(BUCKLEY, keys=[["fury"]],        title="Monomyth – The Fury", moods=["peril"]),
    "passage":          dict(BUCKLEY, keys=[["passage"]],     title="Passage",             moods=["grief", "ice"]),
    "aphelion":         dict(BUCKLEY, keys=[["aphelion"]],    title="Aphelion",            moods=["ice", "voyage"]),
    "never-dying":      dict(BUCKLEY, keys=[["neverdying"]],  title="Never Dying",         moods=["grief", "peril"]),
}

def existing_config(cfg_path):
    """Entries already written to ../index.html, so earlier answers are kept on a re-run."""
    out = {}
    if not os.path.exists(cfg_path): return out
    html = open(cfg_path, encoding="utf-8").read()
    for line in re.findall(r"\{\s*file:\s*\"[^\"]+\"[^\n]*\}", html):
        get = lambda k: (re.search(k + r':\s*"((?:[^"\\]|\\.)*)"', line) or [None, None])[1]
        moods = re.search(r"moods:\s*\[([^\]]*)\]", line)
        gain = re.search(r"gain:\s*([0-9.]+)", line)
        f = get("file")
        if f: out[f] = { "file": f, "title": get("title") or f, "by": get("by") or "", "license": get("license") or "",
                         "moods": re.findall(r'"([a-z]+)"', moods.group(1)) if moods else [], "gain": float(gain.group(1)) if gain else 1 }
    return out
ARTISTS = [  # (pattern in file name, slug prefix, credit, licence)
    (r"scott\s*buckley|scottbuckley", "buckley", "Scott Buckley", "CC BY 4.0"),
]

def norm(s): return re.sub(r"[^a-z0-9]", "", s.lower())
def slug(s):
    s = re.sub(r"\.(mp3|ogg|m4a|wav|flac|opus|aac)$", "", s, flags=re.I)
    s = re.sub(r"^\d+[\s._-]*", "", s)                         # leading track numbers
    s = re.sub(r"[\(\[].*?[\)\]]", " ", s)                      # bracketed notes
    s = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", s)                  # split CamelCase: WithTheseHands -> With These Hands
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s or "track"

def describe(filename):
    """Return (newname_without_ext, entry) for a file, or None if it is not a track."""
    base, ext = os.path.splitext(filename); n = norm(base)
    for name, k in KNOWN.items():
        if any(all(key in n for key in ks) for ks in k["keys"]):
            return name, { "file": None, "title": k["title"], "by": k["by"], "license": k["license"], "moods": list(k["moods"]), "gain": k.get("gain", 1) }
    title, by, lic, prefix = base, "", "", ""
    for pat, pre, artist, licence in ARTISTS:
        if re.search(pat, base, flags=re.I):
            by, lic, prefix = artist, licence, pre + "-"
            title = re.sub(pat, "", base, flags=re.I).strip(" -_–—.")
            break
    title = re.sub(r"^\d+[\s._-]*", "", title).replace("_", " ").strip(" -–—")
    title = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", title)
    return prefix + slug(title), { "file": None, "title": title or base, "by": by or "EDIT ME (performer)", "license": lic or "EDIT ME (licence)", "moods": [], "gain": 1 }

def ask_moods(title, default):
    while True:
        raw = input(f"  moods for \"{title}\" [{', '.join(MOODS)}] (default {','.join(default)}): ").strip()
        if not raw: return default
        chosen = [m.strip().lower() for m in raw.replace(";", ",").split(",") if m.strip()]
        bad = [m for m in chosen if m not in MOODS]
        if not bad: return chosen
        print("    unknown mood(s): " + ", ".join(bad))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--apply", action="store_true"); ap.add_argument("--write-config", action="store_true")
    ap.add_argument("--no-prompt", action="store_true"); ap.add_argument("--default-moods", default="ice")
    ap.add_argument("--ambience", default=None, help="file name to use as the looping sea ambience")
    ap.add_argument("--by", default=None, help="performer credit for unrecognised tracks"); ap.add_argument("--license", default=None, help="licence for unrecognised tracks")
    args = ap.parse_args()
    folder = os.path.abspath(args.dir)
    if not os.path.isdir(folder): print("ERROR: folder not found: " + folder); sys.exit(1)
    default_moods = [m.strip() for m in args.default_moods.split(",") if m.strip() in MOODS] or ["ice"]

    files = sorted(f for f in os.listdir(folder) if os.path.splitext(f)[1].lower() in AUDIO_EXT)
    if not args.ambience:
        amb = [f for f in files if re.search(r"ambien|waves?\b|\bsea\b|ocean|wind|surf|shore", f, flags=re.I) and not f.startswith("sfx-")]
        if len(amb) == 1: args.ambience = amb[0]
        elif len(amb) > 1: print("Several files look like ambience; pick one with --ambience: " + ", ".join(amb)); sys.exit(1)
    cfg_path = os.path.join(os.path.dirname(folder), "index.html")
    previous = existing_config(cfg_path)
    plan, errors, seen = [], [], {}
    for f in files:
        if args.ambience and f == args.ambience: continue
        if f.startswith("sfx-"): continue
        name, entry = describe(f)
        ext0 = os.path.splitext(f)[1].lower()
        if (name + ext0) in previous and "EDIT ME" in entry["by"] + entry["license"]:
            entry = dict(previous[name + ext0])                     # keep what was configured last time
        if "EDIT ME" in entry["by"] and args.by: entry["by"] = args.by
        if "EDIT ME" in entry["license"] and args.license: entry["license"] = args.license
        ext = os.path.splitext(f)[1].lower(); target = name + ext
        if name in seen: errors.append(f"'{f}' and '{seen[name]}' would both become '{target}'"); continue
        seen[name] = f
        entry["file"] = target
        plan.append((f, target, entry))
    if errors:
        print("ERRORS:"); [print("  - " + e) for e in errors]; print("Nothing changed."); sys.exit(1)
    if not plan: print("No audio files found in " + folder); sys.exit(1)

    print(f"Folder: {folder}\n")
    for f, target, entry in plan:
        print(f"  {target:<40} <- {f}" + ("   (already named)" if f == target else ""))
    if args.ambience: print(f"\n  ambience loop: {args.ambience}")

    # moods
    print()
    for f, target, entry in plan:
        if entry["moods"]: continue
        entry["moods"] = default_moods if args.no_prompt else ask_moods(entry["title"], default_moods)

    tracks_js = ",\n".join(
        "      { " + ", ".join([f'file: {json.dumps(e["file"])}', f'title: {json.dumps(e["title"])}', f'by: {json.dumps(e["by"])}', f'license: {json.dumps(e["license"])}', f'moods: {json.dumps(e["moods"])}'] + ([f'gain: {e["gain"]}'] if e["gain"] != 1 else [])) + " }"
        for _, _, e in plan)
    sfx_js = "sfx: { ambience: [" + (json.dumps(args.ambience) if args.ambience else "") + "] }"
    print("\nConfiguration (window.AUDIO_CONFIG.tracks):\n" + tracks_js + "\n    " + sfx_js)
    unedited = [e["file"] for _, _, e in plan if "EDIT ME" in e["by"] + e["license"]]
    if unedited: print("\nFill in performer and licence for: " + ", ".join(unedited))

    if not args.apply:
        print("\nDry run only. Re-run with --apply to rename, and --write-config to update ../index.html."); return
    # check every destination first, so nothing is renamed if any would clash
    for f, target, _ in plan:
        if f == target: continue
        dst = os.path.join(folder, target)
        case_only = f.lower() == target.lower()          # Windows and macOS treat these as the same file
        if os.path.exists(dst) and not case_only: print("ERROR: destination already exists: " + dst + "\nNothing was renamed."); sys.exit(1)
    for f, target, _ in plan:
        if f == target: continue
        src, dst = os.path.join(folder, f), os.path.join(folder, target)
        if f.lower() == target.lower():                   # case-only rename: go via a temporary name
            tmp = dst + ".renaming"; os.rename(src, tmp); os.rename(tmp, dst)
        else:
            os.rename(src, dst)
        print(f"renamed  {f}  ->  {target}")
    if args.write_config:
        cfg = cfg_path
        if not os.path.exists(cfg): print("ERROR: could not find " + cfg); sys.exit(1)
        html = open(cfg, encoding="utf-8").read()
        m = re.search(r"(window\.AUDIO_CONFIG\s*=\s*\{[\s\S]*?tracks:\s*\[)[\s\S]*?(\n\s*\],\s*\n)[\s\S]*?(sfx:\s*\{[^}]*\})", html)
        if not m: print("ERROR: could not find the tracks list in index.html; paste the configuration above by hand"); sys.exit(1)
        html = html[:m.start()] + m.group(1) + "\n" + tracks_js + m.group(2) + "    " + sfx_js + html[m.end():]
        open(cfg, "w", encoding="utf-8").write(html); print("updated " + cfg)
    print("\nDone.")

if __name__ == "__main__":
    main()

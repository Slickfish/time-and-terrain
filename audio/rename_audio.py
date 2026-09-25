#!/usr/bin/env python3
"""
rename_audio.py — rename the downloaded Old Guard Fife and Drum Corps tracks to the file names
the Revolutionary War map expects (see window.AUDIO_CONFIG in revolutionary-war/index.html).

Usage
  python rename_audio.py                 dry run: shows what would be renamed, errors if anything is unmatched
  python rename_audio.py --apply         actually rename the files
  python rename_audio.py --apply --fix-config
                                         also rewrite the file extensions in ../index.html if your files are
                                         .ogg or .m4a rather than .mp3
  python rename_audio.py --dir "C:\\path\\to\\audio"   run against another folder (default: the script's folder)

Rules
  * Every expected track must match exactly one file, and every matched file exactly one track.
    Anything else is reported and the script exits with code 1 without touching a file.
  * Files that already carry an expected name are left alone.
  * Other files in the folder (sound effects, READMEs) are ignored.
"""
import argparse, os, re, sys

# expected name (without extension) -> list of alternative keyword sets; a file matches if ALL keywords of ANY set
# occur in its normalised name (lower-case letters and digits only)
TARGETS = {
    "old-guard-reveille-yankee-doodle":            [["reveille", "yankee"], ["reveille", "drumcall"], ["yankeedoodle"]],
    "old-guard-brandywine-quickstep":              [["brandywine"]],
    "old-guard-fishers-hornpipe":                  [["fisher", "hornpipe"], ["guilderoy"], ["redhaired"]],
    "old-guard-soldiers-farewell-march-of-war":    [["soldier", "farewell"], ["windsorpark"], ["marchofwar"]],
    "old-guard-presidents-march-death-of-wolfe":   [["president", "march"], ["generalwolf"], ["rightsofman"]],
    "old-guard-rage-of-cornwallis":                [["cornwallis"]],
    "old-guard-three-little-drummers":             [["three", "little", "drummer"]],
    "old-guard-water-music":                       [["water", "music"]],
    "old-guard-boismortier-adagio":                [["boismortier", "adagio"]],
    "old-guard-boismortier-allegro":               [["boismortier", "allegro"]],
    "old-guard-pezel-twist":                       [["pezel"]],
}
AUDIO_EXT = {".mp3", ".ogg", ".m4a", ".wav", ".flac", ".opus", ".aac"}

def norm(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())

def matches(target, filename):
    n = norm(os.path.splitext(filename)[0])
    return any(all(k in n for k in keyset) for keyset in TARGETS[target])

def main():
    ap = argparse.ArgumentParser(description="Rename Old Guard tracks for the Revolutionary War map.")
    ap.add_argument("--dir", default=os.path.dirname(os.path.abspath(__file__)), help="folder containing the downloaded files")
    ap.add_argument("--apply", action="store_true", help="perform the renames (default is a dry run)")
    ap.add_argument("--fix-config", action="store_true", help="rewrite extensions in ../index.html to match the renamed files")
    args = ap.parse_args()
    folder = os.path.abspath(args.dir)
    if not os.path.isdir(folder):
        print(f"ERROR: folder not found: {folder}"); sys.exit(1)

    files = [f for f in os.listdir(folder) if os.path.splitext(f)[1].lower() in AUDIO_EXT]
    already = {os.path.splitext(f)[0]: f for f in files if os.path.splitext(f)[0] in TARGETS}
    candidates = [f for f in files if os.path.splitext(f)[0] not in TARGETS]

    plan, errors = {}, []
    for target in TARGETS:
        if target in already:
            plan[target] = ("keep", already[target]); continue
        hits = [f for f in candidates if matches(target, f)]
        if len(hits) == 1:
            plan[target] = ("rename", hits[0])
        elif not hits:
            errors.append(f"no file matches '{target}'  (looking for: " + " | ".join(" + ".join(k) for k in TARGETS[target]) + ")")
        else:
            errors.append(f"several files match '{target}': " + ", ".join(hits))
    # one file must not serve two targets
    used = {}
    for target, (action, f) in plan.items():
        if action == "rename":
            used.setdefault(f, []).append(target)
    for f, ts in used.items():
        if len(ts) > 1:
            errors.append(f"'{f}' matches more than one expected track: " + ", ".join(ts))
    unmatched = [f for f in candidates if f not in used]

    width = max(len(t) for t in TARGETS) + 4
    print(f"Folder: {folder}\n")
    for target, (action, f) in plan.items():
        ext = os.path.splitext(f)[1].lower()
        print(f"  {target + ext:<{width}} <- {f}" + ("   (already named)" if action == "keep" else ""))
    if unmatched:
        print("\nIgnored (not recognised as one of the expected tracks):")
        for f in unmatched: print("  " + f)
    if errors:
        print("\nERRORS:")
        for e in errors: print("  - " + e)
        print("\nNothing was renamed. Fix the problems above and run again.")
        sys.exit(1)

    exts = {os.path.splitext(f)[1].lower() for _, f in plan.values()}
    if not args.apply:
        print("\nDry run only. Re-run with --apply to rename." + ("" if exts == {".mp3"} else "\nNote: your files are " + ", ".join(sorted(exts)) + "; the page expects .mp3 names. Add --fix-config to update index.html, or convert the files."))
        return

    for target, (action, f) in plan.items():
        if action == "keep": continue
        ext = os.path.splitext(f)[1].lower()
        dst = os.path.join(folder, target + ext)
        if os.path.exists(dst):
            print(f"ERROR: destination already exists: {dst}"); sys.exit(1)
        os.rename(os.path.join(folder, f), dst)
        print(f"renamed  {f}  ->  {target + ext}")

    if args.fix_config:
        cfg = os.path.join(os.path.dirname(folder), "index.html")
        if not os.path.exists(cfg):
            print(f"ERROR: could not find {cfg} to fix the configuration"); sys.exit(1)
        html = open(cfg, encoding="utf-8").read(); changed = 0
        for target, (action, f) in plan.items():
            ext = os.path.splitext(f)[1].lower()
            for old_ext in AUDIO_EXT:
                token = f'"{target}{old_ext}"'
                if old_ext != ext and token in html:
                    html = html.replace(token, f'"{target}{ext}"'); changed += 1
        if changed:
            open(cfg, "w", encoding="utf-8").write(html)
            print(f"updated {changed} file name(s) in {cfg}")
        else:
            print("index.html already matches the file extensions.")
    elif exts != {".mp3"}:
        print("\nNote: the page expects .mp3 names but your files are " + ", ".join(sorted(exts)) + ". Run again with --fix-config, or edit window.AUDIO_CONFIG in index.html.")
    print("\nDone.")

if __name__ == "__main__":
    main()

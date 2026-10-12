"""Small, dependency-free helper for a personal LeetCode journal."""

from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT))
from tools import cpp_runner, leetcode_api

START = "<!-- PROGRESS:START -->"
END = "<!-- PROGRESS:END -->"
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
DIFFICULTIES = ("Easy", "Medium", "Hard")
STATUSES = ("planned", "in-progress", "solved")


def validate(data: dict) -> None:
    if not isinstance(data, dict):
        raise ValueError("problem.json must contain a JSON object")
    if type(data.get("id")) is not int or data["id"] < 1:
        raise ValueError("id must be a positive integer")
    if not isinstance(data.get("slug"), str) or not SLUG.fullmatch(data["slug"]):
        raise ValueError("slug must use lowercase letters, digits, and single hyphens")
    if not isinstance(data.get("title"), str) or not data["title"].strip():
        raise ValueError("title must be nonempty")
    if any(char in data["title"] for char in "\r\n"):
        raise ValueError("title must fit on one line")
    if data.get("difficulty") not in DIFFICULTIES:
        raise ValueError("difficulty must be Easy, Medium, or Hard")
    if data.get("status") not in STATUSES:
        raise ValueError("status must be planned, in-progress, or solved")
    topics = data.get("topics")
    if not isinstance(topics, list) or any(
        not isinstance(topic, str) or not SLUG.fullmatch(topic) for topic in topics
    ):
        raise ValueError("topics must be a list of lowercase hyphenated tags")
    solved_on = data.get("solved_on")
    if data["status"] == "solved":
        if not isinstance(solved_on, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", solved_on):
            raise ValueError("a solved problem needs solved_on in YYYY-MM-DD format")
        date.fromisoformat(solved_on)
    elif solved_on is not None:
        raise ValueError("solved_on must be null until the problem is solved")


def load_problems(root: Path = ROOT) -> list[tuple[Path, dict]]:
    problems = []
    seen = set()
    for folder in sorted((root / "problems").iterdir()):
        if not folder.is_dir() or folder.name.startswith("."):
            continue
        try:
            data = json.loads((folder / "problem.json").read_text(encoding="utf-8"))
            validate(data)
            expected = f"{data['id']:04d}-{data['slug']}"
            if folder.name != expected:
                raise ValueError(f"folder name must be {expected}")
            if data["id"] in seen:
                raise ValueError(f"duplicate problem id: {data['id']}")
            if not (folder / "solution.cpp").is_file() or not (folder / "README.md").is_file():
                raise ValueError("each problem needs solution.cpp and README.md")
            seen.add(data["id"])
            problems.append((folder, data))
        except (ValueError, OSError) as error:
            raise ValueError(f"{folder.name}: {error}") from error
    return sorted(problems, key=lambda item: item[1]["id"])


def markdown(value: str) -> str:
    for char in ("\\", "|", "[", "]", "<", ">", "*", "_", "`"):
        value = value.replace(char, "\\" + char)
    return value


def read_profile(root: Path) -> dict | None:
    snapshot = root / "progress" / "leetcode.json"
    if not snapshot.exists():
        return None
    profile = json.loads(snapshot.read_text(encoding="utf-8"))
    counts = profile["solved"]
    if set(counts) != {"All", "Easy", "Medium", "Hard"} or any(type(value) is not int or value < 0 for value in counts.values()):
        raise ValueError("Invalid cached LeetCode counters")
    if counts["All"] != sum(counts[level] for level in DIFFICULTIES):
        raise ValueError("Inconsistent cached LeetCode counters")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", profile["username"]):
        raise ValueError("Invalid cached LeetCode username")
    configured = json.loads((root / "leetcode.json").read_text(encoding="utf-8"))["username"]
    if configured != profile["username"]:
        raise ValueError("Cached profile belongs to a different username; run sync")
    return profile


def render_progress(problems: list[tuple[Path, dict]], profile: dict | None = None) -> str:
    solved = [data for _, data in problems if data["status"] == "solved"]
    active = sum(data["status"] == "in-progress" for _, data in problems)
    planned = sum(data["status"] == "planned" for _, data in problems)
    counts = {level: sum(data["difficulty"] == level for data in solved) for level in DIFFICULTIES}
    lines = []
    if profile:
        account = profile["solved"]
        username = profile["username"]
        lines.extend([
            f"### LeetCode account · [{username}](https://leetcode.com/u/{username}/)",
            "",
            f"**{account['All']} solved on LeetCode**",
            "",
            "| Easy | Medium | Hard |",
            "| :---: | :---: | :---: |",
            f"| {account['Easy']} | {account['Medium']} | {account['Hard']} |",
            "",
            f"Snapshot updated: {profile['updated_at']} (UTC). Includes earlier solutions outside this repository.",
            "",
        ])
    lines.extend([
        "### Repository journal",
        "",
        f"**{len(solved)} solved** · **{active} in progress** · **{planned} planned**",
        "",
        "| Easy solved | Medium solved | Hard solved |",
        "| :---: | :---: | :---: |",
        f"| {counts['Easy']} | {counts['Medium']} | {counts['Hard']} |",
        "",
    ])
    if not problems:
        lines.append("The journal is ready. The first problem will appear here when I start practicing.")
    else:
        lines.extend([
            "| # | Problem | Difficulty | Topics | Status | Solved on |",
            "| --- | --- | --- | --- | --- | --- |",
        ])
        labels = {"planned": "Planned", "in-progress": "In progress", "solved": "Accepted"}
        for folder, data in problems:
            title = markdown(data["title"])
            topics = ", ".join(data["topics"]) or "—"
            lines.append(
                f"| {data['id']} | [{title}](problems/{folder.name}/) | {data['difficulty']} "
                f"| {topics} | {labels[data['status']]} | {data.get('solved_on') or '—'} |"
            )
    return "\n".join(lines)


def refresh(root: Path = ROOT, *, check: bool = False) -> None:
    problems = load_problems(root)
    readme = root / "README.md"
    original = readme.read_text(encoding="utf-8")
    if original.count(START) != 1 or original.count(END) != 1:
        raise ValueError("README.md needs exactly one pair of progress markers")
    before, tail = original.split(START, 1)
    if END not in tail:
        raise ValueError("progress markers are out of order")
    _, after = tail.split(END, 1)
    updated = before + START + "\n" + render_progress(problems, read_profile(root)) + "\n" + END + after
    if check and original != updated:
        raise ValueError("Progress is outdated. Run: python tools/leetcode.py refresh")
    if not check and original != updated:
        readme.write_text(updated, encoding="utf-8", newline="\n")


def new_problem(args: argparse.Namespace, root: Path = ROOT, *, question: dict | None = None) -> Path:
    data = {
        "id": args.id,
        "slug": args.slug,
        "title": args.title.strip(),
        "difficulty": args.difficulty,
        "status": "in-progress",
        "topics": sorted(set(args.topics)),
        "solved_on": None,
    }
    validate(data)
    existing = load_problems(root)
    if any(problem["id"] == args.id for _, problem in existing):
        raise ValueError(f"Problem {args.id} already exists")
    folder = root / "problems" / f"{args.id:04d}-{args.slug}"
    template = root / "templates" / "cpp"
    # Read everything before creating the folder; malformed templates leave no partial task.
    sources = {name: (template / name).read_text(encoding="utf-8") for name in ("solution.cpp", "main.cpp")}
    if question:
        signature = question["signature"]
        data["signature"] = signature
        try:
            cases = cpp_runner.parse_examples(question["exampleTestcases"], signature)
        except (ValueError, TypeError):
            cases = []
        driver, reason = cpp_runner.make_driver(signature, cases)
        data["runner"] = "manual" if reason else "automatic"
        sources.update({
            "solution.cpp": cpp_runner.solution_source(question["cpp"]),
            "main.cpp": cpp_runner.MAIN,
            "types.hpp": cpp_runner.local_types(question["cpp"]),
            "cases.json": json.dumps(cases, ensure_ascii=False, indent=2) + "\n",
            "cases.generated.hpp": driver,
        })
    description = (template / "README.md").read_text(encoding="utf-8").format(
        id=args.id,
        title=markdown(data["title"]),
        difficulty=args.difficulty,
        problem_url=f"https://leetcode.com/problems/{args.slug}/",
    )
    folder.mkdir()
    for name, content in sources.items():
        (folder / name).write_text(content, encoding="utf-8", newline="\n")
    (folder / "README.md").write_text(description, encoding="utf-8", newline="\n")
    (folder / "problem.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    refresh(root)
    return folder


def new_online(slug: str, root: Path = ROOT) -> Path:
    if not SLUG.fullmatch(slug):
        raise ValueError("Use the problem slug, for example add-two-numbers")
    # Do not fetch or overwrite anything for an existing folder.
    if any(data["slug"] == slug for _, data in load_problems(root)):
        raise ValueError(f"Problem already exists: {slug}")
    question = leetcode_api.fetch_question(slug)
    args = argparse.Namespace(
        id=int(question["questionFrontendId"]), slug=question["titleSlug"],
        title=question["title"], difficulty=question["difficulty"],
        topics=[tag["slug"] for tag in question["topicTags"]],
    )
    return new_problem(args, root, question=question)


def find_problem(key: int | str, root: Path = ROOT) -> tuple[Path, dict]:
    for folder, data in load_problems(root):
        if str(data["id"]) == str(key) or str(key) in (data["slug"], folder.name):
            return folder, data
    raise ValueError(f"Problem {key} does not exist")


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def mark_done(problem_id: int | str, root: Path = ROOT) -> Path:
    folder, data = find_problem(problem_id, root)
    data["status"] = "solved"
    data["solved_on"] = data.get("solved_on") or date.today().isoformat()
    write_json(folder / "problem.json", data)
    refresh(root)
    return folder


def sync_profile(root: Path = ROOT) -> dict:
    problems = load_problems(root)
    config = json.loads((root / "leetcode.json").read_text(encoding="utf-8"))
    username = config["username"]
    if not isinstance(username, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", username):
        raise ValueError("Invalid username in leetcode.json")
    # Validate the README before the request or any writes.
    text = (root / "README.md").read_text(encoding="utf-8")
    if text.count(START) != 1 or text.count(END) != 1 or text.index(START) > text.index(END):
        raise ValueError("Invalid README progress markers")
    profile = leetcode_api.fetch_profile(username)
    if profile["username"] != username:
        raise ValueError("LeetCode returned a different account")
    snapshot = root / "progress" / "leetcode.json"
    old = json.loads(snapshot.read_text(encoding="utf-8")) if snapshot.exists() else None
    previous = {key: value for key, value in old.items() if key != "updated_at"} if old else None
    if previous != profile:
        profile["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
        snapshot.parent.mkdir(exist_ok=True)
        write_json(snapshot, profile)
    else:
        profile = old
    recent = {item["titleSlug"]: item for item in sorted(profile["recent_accepted"], key=lambda item: int(item["timestamp"]), reverse=True)}
    for folder, data in problems:
        submission = recent.get(data["slug"])
        source = (folder / "solution.cpp").read_text(encoding="utf-8")
        starter = "Implement the LeetCode method first" in source or source == (root / "templates/cpp/solution.cpp").read_text(encoding="utf-8")
        if submission and data["status"] != "solved" and not starter:
            data["status"] = "solved"
            data["solved_on"] = date.fromtimestamp(int(submission["timestamp"])).isoformat()
            data["status_source"] = "leetcode-public"
            data["accepted_submission_id"] = str(submission["id"])
            write_json(folder / "problem.json", data)
    refresh(root)
    return profile


def generate_driver(key: str, root: Path = ROOT) -> Path:
    folder, data = find_problem(key, root)
    if "signature" not in data:
        raise ValueError("This is an offline template; edit main.cpp manually")
    cases = json.loads((folder / "cases.json").read_text(encoding="utf-8"))
    if data.get("runner") == "manual":
        # Never replace a manual main.cpp or generate calls for a custom judge.
        content, _ = cpp_runner.make_driver({"manual": True}, cases)
    else:
        content = cpp_runner.render_driver(data["signature"], cases)
    path = folder / "cases.generated.hpp"
    if not path.exists() or path.read_text(encoding="utf-8") != content:
        path.write_text(content, encoding="utf-8", newline="\n")
    return path


def run_problem(key: str, root: Path = ROOT) -> int:
    folder, data = find_problem(key, root)
    if "signature" in data:
        generate_driver(key, root)
    compiler = shutil.which("g++") or shutil.which("clang++")
    compiler_dir = None
    if not compiler:
        # The user's existing CLion installation; no global PATH changes.
        candidates = sorted(Path("E:/Progs").glob("CLion*/bin/mingw/bin/g++.exe"))
        if candidates:
            compiler = str(candidates[-1])
            compiler_dir = str(candidates[-1].parent)
    if not compiler:
        raise ValueError("C++ compiler not found. Run in CLion, or put g++/clang++ on PATH")
    import os
    env = os.environ.copy()
    if compiler_dir:
        env["PATH"] = compiler_dir + os.pathsep + env.get("PATH", "")
    output = root / "build" / "runners"
    output.mkdir(parents=True, exist_ok=True)
    executable = output / (folder.name + (".exe" if sys.platform == "win32" else ""))
    subprocess.run([compiler, "-std=c++17", "-Wall", "-Wextra", "-Wpedantic", str(folder / "main.cpp"), "-o", str(executable)], env=env, check=True)
    return subprocess.run([str(executable)], env=env).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    new = commands.add_parser("new", help="create a C++ problem folder")
    new.add_argument("target", help="slug, or numeric ID followed by slug for the offline template")
    new.add_argument("legacy_slug", nargs="?")
    new.add_argument("--title")
    new.add_argument("--difficulty", choices=DIFFICULTIES)
    new.add_argument("--topics", nargs="*", default=[])
    done = commands.add_parser("done", help="mark a problem solved after an Accepted submission")
    done.add_argument("id", help="problem ID or slug")
    commands.add_parser("sync", help="sync public LeetCode counters and recent Accepted statuses")
    commands.add_parser("import-browser", help="import Accepted code uploaded by the browser extension")
    driver = commands.add_parser("driver", help="regenerate local calls from cases.json (also used by CMake)")
    driver.add_argument("target")
    run = commands.add_parser("run", help="compile and run a local problem without reading stdin")
    run.add_argument("target")
    commands.add_parser("refresh", help="refresh the progress table")
    commands.add_parser("check", help="validate metadata and check that progress is up to date")
    args = parser.parse_args()
    try:
        if args.command == "new":
            if args.legacy_slug is not None:
                if not args.title or not args.difficulty:
                    raise ValueError("Offline creation needs --title and --difficulty")
                args.id, args.slug = int(args.target), args.legacy_slug
                folder = new_problem(args)
            else:
                folder = new_online(args.target)
            print(f"Created: {folder}")
        elif args.command == "done":
            print(f"Marked solved: {mark_done(args.id)}")
        elif args.command == "sync":
            profile = sync_profile()
            print(f"Synced {profile['username']}: {profile['solved']['All']} solved on LeetCode")
        elif args.command == "import-browser":
            from tools.browser_import import import_browser
            changed = import_browser(ROOT)
            print("Imported: " + ", ".join(changed) if changed else "Browser archive is already up to date.")
        elif args.command == "driver":
            print(f"Generated: {generate_driver(args.target)}")
        elif args.command == "run":
            return run_problem(args.target)
        else:
            refresh(check=args.command == "check")
            print("Progress is valid and up to date." if args.command == "check" else "Progress refreshed.")
        return 0
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

"""Import AlgoVault's Accepted archive without losing local work or notes."""

from datetime import date
import hashlib
import json
from pathlib import Path
import re

from tools import cpp_runner, leetcode_api

FOLDER = re.compile(r"([0-9]+)-([a-z0-9]+(?:-[a-z0-9]+)*)")
FILE = re.compile(r"solution(?:_([2-9]|[1-9][0-9]+))?\.(cpp|py|js|ts|java|rs|go|c|cs|kt|swift|rb|sql|dart|php|ex|scala)")


def digest(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def import_browser(root: Path) -> list[str]:
    # Import here to avoid a cycle with the command-line entry point.
    from tools import leetcode

    inbox = root / "browser-sync"
    if not inbox.exists():
        return []
    if inbox.is_symlink() or inbox.resolve() != root.resolve() / "browser-sync":
        raise ValueError("Browser archive must stay inside the repository")
    problems = leetcode.load_problems(root)
    changed = []
    for incoming in sorted(inbox.iterdir()):
        if not incoming.is_dir():
            continue
        if incoming.is_symlink() or incoming.resolve().parent != inbox.resolve():
            raise ValueError("Browser archive folders must stay inside browser-sync")
        match = FOLDER.fullmatch(incoming.name)
        if not match:
            raise ValueError(f"Invalid browser archive folder: {incoming.name}")
        problem_id, slug = int(match[1]), match[2]
        sources = []
        for path in incoming.iterdir():
            filename = FILE.fullmatch(path.name)
            if filename:
                if path.is_symlink() or not path.is_file():
                    raise ValueError("Browser solution must be an ordinary file")
                content = path.read_text(encoding="utf-8-sig")
                if not content.strip():
                    raise ValueError(f"Empty browser solution: {path.name}")
                sources.append((int(filename[1] or 1), path.name, filename[2], content))
        if not sources:
            # README and solution may arrive in separate commits from another exporter.
            continue
        existing = [(folder, data) for folder, data in problems if data["id"] == problem_id or data["slug"] == slug]
        if existing:
            folder, data = existing[0]
            if data["id"] != problem_id or data["slug"] != slug:
                raise ValueError("Browser folder conflicts with an existing problem's id or slug")
        else:
            question = leetcode_api.fetch_question(slug)
            if int(question["questionFrontendId"]) != problem_id:
                raise ValueError("Browser problem number does not match LeetCode")
            import argparse
            args = argparse.Namespace(id=problem_id, slug=slug, title=question["title"], difficulty=question["difficulty"], topics=[tag["slug"] for tag in question["topicTags"]])
            folder = leetcode.new_problem(args, root, question=question)
            data = json.loads((folder / "problem.json").read_text(encoding="utf-8"))
            problems.append((folder, data))
        before = json.dumps(data, sort_keys=True)
        if folder.is_symlink() or folder.resolve().parent != (root / "problems").resolve():
            raise ValueError("Problem folder must stay inside problems")
        archive = folder / "accepted"
        if archive.exists() and (archive.is_symlink() or archive.resolve().parent != folder.resolve()):
            raise ValueError("Accepted archive must stay inside the problem folder")
        archive.mkdir(exist_ok=True)
        state = data.setdefault("browser_sync", {"files": {}})
        file_changed = False
        for _, name, _, content in sorted(sources):
            target = archive / name
            if target.is_symlink():
                raise ValueError("Accepted solution must not be a symlink")
            if target.exists() and target.read_text(encoding="utf-8") != content:
                # A user may have annotated an imported copy: retain both versions.
                alternate = archive / (Path(name).stem + "_" + digest(content)[:12] + Path(name).suffix)
                if alternate.is_symlink():
                    raise ValueError("Accepted solution must not be a symlink")
                if alternate.exists() and alternate.read_text(encoding="utf-8") != content:
                    raise ValueError("An accepted archive name is already occupied")
                target = alternate
            if not target.exists():
                target.write_text(content, encoding="utf-8", newline="\n")
                file_changed = True
            state["files"][name] = {"sha256": digest(content), "saved_as": target.relative_to(folder).as_posix()}
        cpp_sources = [source for source in sources if source[2] == "cpp"]
        if cpp_sources:
            _, latest_name, _, latest_code = max(cpp_sources)
            primary = folder / "solution.cpp"
            if primary.is_symlink():
                raise ValueError("Primary solution must not be a symlink")
            current = primary.read_text(encoding="utf-8")
            offline = (root / "templates/cpp/solution.cpp").read_text(encoding="utf-8")
            may_replace = "Implement the LeetCode method first" in current or current == offline or digest(current) == state.get("primary_sha256")
            if may_replace:
                updated = cpp_runner.HEADERS + latest_code.rstrip("\n") + "\n"
                if current != updated:
                    primary.write_text(updated, encoding="utf-8", newline="\n")
                    file_changed = True
                state["primary_sha256"] = digest(updated)
            state["latest_cpp"] = state["files"][latest_name]["saved_as"]
        data["status"] = "solved"
        data["solved_on"] = data.get("solved_on") or date.today().isoformat()
        data.setdefault("solved_on_source", "first-browser-import")
        data["status_source"] = "browser-extension"
        if before != json.dumps(data, sort_keys=True):
            leetcode.write_json(folder / "problem.json", data)
            file_changed = True
        if file_changed:
            changed.append(folder.name)
    # AlgoVault 0.1.1's topic links use master even when its commit branch is main.
    # Repair only links into our own browser archive, preserving the rest of README.
    readme = root / "README.md"
    text = readme.read_text(encoding="utf-8")
    fixed = text.replace(
        "https://github.com/dormyyy/leetcode-lab/tree/master/browser-sync/",
        "https://github.com/dormyyy/leetcode-lab/tree/main/browser-sync/",
    )
    if fixed != text:
        readme.write_text(fixed, encoding="utf-8", newline="\n")
    leetcode.refresh(root)
    return changed

"""Read the public GraphQL data used by leetcode.com itself."""

import json
import urllib.error
import urllib.request

ENDPOINT = "https://leetcode.com/graphql/"


def graphql(query: str, variables: dict) -> dict:
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps({"query": query, "variables": variables}).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "leetcode-lab/1.0",
            "Referer": "https://leetcode.com/",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            payload = json.load(response)
    except (urllib.error.URLError, TimeoutError, ValueError) as error:
        raise ValueError(f"LeetCode request failed; existing files are kept: {error}") from error
    if payload.get("errors") or not isinstance(payload.get("data"), dict):
        raise ValueError("LeetCode returned an error or changed its public GraphQL schema")
    return payload["data"]


def fetch_question(slug: str) -> dict:
    data = graphql("""
        query($slug: String!) {
          question(titleSlug: $slug) {
            questionFrontendId title titleSlug difficulty isPaidOnly
            codeSnippets { langSlug code }
            metaData exampleTestcases topicTags { slug }
          }
        }
    """, {"slug": slug})
    question = data.get("question")
    if not question:
        raise ValueError(f"LeetCode problem not found: {slug}")
    if question.get("isPaidOnly"):
        raise ValueError("This problem requires Premium; use the offline template for your own code")
    try:
        question["cpp"] = next(item["code"] for item in question["codeSnippets"] if item["langSlug"] == "cpp")
        question["signature"] = json.loads(question["metaData"])
        int(question["questionFrontendId"])
    except (KeyError, StopIteration, TypeError, ValueError) as error:
        raise ValueError("This problem does not expose a supported numbered C++ template") from error
    return question


def fetch_profile(username: str) -> dict:
    data = graphql("""
        query($username: String!) {
          matchedUser(username: $username) {
            username submitStatsGlobal { acSubmissionNum { difficulty count } }
          }
          recentAcSubmissionList(username: $username, limit: 20) {
            id titleSlug timestamp
          }
        }
    """, {"username": username})
    user = data.get("matchedUser")
    if not user:
        raise ValueError(f"LeetCode profile not found: {username}")
    try:
        counts = {item["difficulty"]: item["count"] for item in user["submitStatsGlobal"]["acSubmissionNum"]}
        if set(counts) != {"All", "Easy", "Medium", "Hard"} or any(type(value) is not int or value < 0 for value in counts.values()):
            raise ValueError("invalid counters")
        if counts["All"] != sum(counts[level] for level in ("Easy", "Medium", "Hard")):
            raise ValueError("inconsistent counters")
        recent = data["recentAcSubmissionList"]
        for item in recent:
            if not isinstance(item["titleSlug"], str):
                raise ValueError("invalid submission slug")
            int(item["timestamp"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("LeetCode returned invalid profile data; cached counters are kept") from error
    return {"username": user["username"], "solved": counts, "recent_accepted": recent}

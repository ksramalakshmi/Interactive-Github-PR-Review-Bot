from collections import defaultdict

# Severity ranking
SEVERITY_ORDER = {
    "none": 0,
    "low": 1,
    "medium": 2,
    "high": 3
}

def deduplicate_findings(findings):
    """
    Groups findings by (file, line) and merges agent comments.
    
    Each finding should have:
        - file
        - line
        - agent
        - severity
        - comment
        - suggestion (optional)
    """
    grouped = defaultdict(list)

    # Group by file + line
    for f in findings:
        key = (f["file"], f["line"])
        grouped[key].append(f)

    merged = []

    for (file, line), group in grouped.items():
        merged.append({
            "file": file,
            "line": line,
            "agents": [g["agent"] for g in group],
            "severity": _max_severity(group),
            "comment": _merge_comments(group),
            "suggestion": _merge_suggestions(group)
        })

    return merged


def _max_severity(group):
    """Return the max severity among grouped findings."""
    return max(
        (g.get("severity", "low") for g in group),
        key=lambda s: SEVERITY_ORDER.get(s, 1)
    )


def _merge_comments(group):
    """Merge multiple comments into one readable string."""
    unique_comments = list(dict.fromkeys(g["comment"] for g in group if g.get("comment")))

    if len(unique_comments) == 1:
        return unique_comments[0]

    merged = "Multiple concerns detected:\n"
    for c in unique_comments:
        merged += f"- {c}\n"

    return merged.strip()


def _merge_suggestions(group):
    """Merge multiple suggestions into one string."""
    suggestions = [g.get("suggestion") for g in group if g.get("suggestion")]
    if not suggestions:
        return None

    unique = list(dict.fromkeys(suggestions))
    if len(unique) == 1:
        return unique[0]

    return "Consider the following:\n" + "\n".join(f"- {s}" for s in unique)
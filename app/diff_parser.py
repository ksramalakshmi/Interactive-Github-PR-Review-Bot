from unidiff import PatchSet

def extract_added_lines(diff_text):
    """
    Returns:
    [
      {
        "file": "app/auth.py",
        "line": 12,
        "code": "password = request['json']['password']"
      }
    ]
    """
    patch = PatchSet(diff_text)
    results = []

    for file in patch:
        for hunk in file:
            for line in hunk:
                if line.is_added:
                    results.append({
                        "file": file.path,
                        "line": line.target_line_no,
                        "code": line.value.strip()
                    })

    return results
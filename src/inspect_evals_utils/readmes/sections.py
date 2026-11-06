"""Generic script to add missing section tags to eval READMEs.

This script scans all eval READMEs and adds HTML comment tags for auto-generated
sections if they don't already exist. It can intelligently place the new section
after a specified list of existing sections (in priority order).

Usage:
    inspect-evals-readmes add-section --key Parameters --insert-after Options --insert-after Usage

The script will:
1. Discover all eval paths from individual eval.yaml files
2. Check each README to see if the section tags already exist
3. If not, insert the tags after the first found section from --insert-after list
4. If none of those sections exist, append to the end of the file

Note: ": Automatically Generated" is automatically appended to all keys.

Adapted from:
https://github.com/UKGovernmentBEIS/inspect_evals/blob/main/tools/add_readme_section.py
"""

from pathlib import Path

import yaml


def normalize_key(key: str) -> str:
    """Normalize a key by ensuring it ends with ': Automatically Generated'.

    Args:
        key: The base key (e.g., "Parameters" or "Parameters: Automatically Generated")

    Returns:
        Normalized key with the suffix
    """
    suffix = ": Automatically Generated"
    if key.endswith(suffix):
        return key
    return f"{key}{suffix}"


def has_section_tags(readme_path: Path, key: str) -> bool:
    """Check if a README already has the specified section tags.

    Args:
        readme_path: Path to the README file
        key: The section key (will be normalized)

    Returns:
        True if the section tags exist, False otherwise
    """
    if not readme_path.exists():
        return False

    normalized_key = normalize_key(key)
    start_tag = f"<!-- {normalized_key} -->"
    content = readme_path.read_text(encoding="utf-8")
    return start_tag in content


def find_insertion_point(lines: list[str], insert_after_keys: list[str]) -> int | None:
    """Find the line index where the new section should be inserted.

    For each key (in priority order), tries two strategies:
    1. Look for HTML comment tag (e.g., <!-- /Options: Automatically Generated -->)
    2. Look for markdown header (e.g., ## Options)

    Args:
        lines: List of lines from the README
        insert_after_keys: List of section keys to try inserting after (in priority order)

    Returns:
        Line index to insert after, or None if no matching section found
    """
    for key in insert_after_keys:
        normalized_key = normalize_key(key)
        section_name = key.replace(": Automatically Generated", "")

        # Strategy 1: Look for HTML comment tag
        end_tag = f"<!-- /{normalized_key} -->"
        for i, line in enumerate(lines):
            if line.strip() == end_tag:
                return i + 1

        # Strategy 2: Look for markdown header
        header = f"## {section_name}"
        for i, line in enumerate(lines):
            if line.strip() == header:
                # Found the header, now find the end of this section
                # Look for the next ## header or end of file
                in_code_block = False
                for j in range(i + 1, len(lines)):
                    next_line = lines[j].strip()

                    # Track code block boundaries (triple backticks)
                    if next_line.startswith("```"):
                        in_code_block = not in_code_block
                        continue

                    # Only check for headers if we're not in a code block
                    if not in_code_block and (next_line.startswith(("## ", "# "))):
                        return j
                # If no next section found, insert at end
                return len(lines)

    return None


def add_section_tags(readme_path: Path, key: str, insert_after_keys: list[str]) -> bool:
    """Add section tags to a README if they don't already exist.

    Args:
        readme_path: Path to the README file
        key: The section key to add (will be normalized)
        insert_after_keys: List of section keys to try inserting after (in priority order)

    Returns:
        True if tags were added, False if they already existed or README doesn't exist
    """
    if not readme_path.exists():
        return False

    if has_section_tags(readme_path, key):
        return False

    # Read the file
    content = readme_path.read_text(encoding="utf-8")
    lines = content.rstrip("\n").split("\n")

    # Create the tags
    normalized_key = normalize_key(key)
    start_tag = f"<!-- {normalized_key} -->"
    end_tag = f"<!-- /{normalized_key} -->"

    # Find insertion point
    insert_index = find_insertion_point(lines, insert_after_keys)

    # If no insertion point found, append to end
    if insert_index is None:
        insert_index = len(lines)

    # Insert the tags with proper spacing
    new_lines = [*lines[:insert_index], "", start_tag, end_tag, *lines[insert_index:]]

    # Write back to file
    readme_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    return True


def _discover_eval_dirs(src_dir: Path) -> list[dict[str, str]]:
    """Discover eval directories by finding eval.yaml files under src/.

    Args:
        src_dir: The src/ directory to scan.

    Returns:
        List of dicts with 'path' and 'title' keys.
    """
    listings = []
    for eval_yaml in sorted(src_dir.glob("*/eval.yaml")):
        if eval_yaml.parent.name == "examples":
            continue
        with open(eval_yaml, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        eval_name = eval_yaml.parent.name
        listings.append(
            {
                "path": str(eval_yaml.parent),
                "title": data.get("title", eval_name),
            }
        )
    return listings


def add_section(src_dir: Path, key: str, insert_after: list[str]) -> list[Path]:
    """Add the tags for `key` to every eval README under `src_dir` that lacks them.

    Args:
        src_dir: Directory holding `<eval>/eval.yaml` packages.
        key: Section key, e.g. "Parameters"; ": Automatically Generated" is appended.
        insert_after: Section keys to insert after, in priority order. If none is
            found, the tags are appended to the end of the file.

    Returns:
        The README paths that gained the tags.
    """
    added: list[Path] = []
    for listing in _discover_eval_dirs(src_dir):
        readme_path = Path(listing["path"]) / "README.md"
        if not readme_path.exists():
            print(f"  MISSING  {listing['title']}: {readme_path}")
        elif has_section_tags(readme_path, key):
            print(f"  SKIP     {listing['title']}: already has section tags")
        elif add_section_tags(readme_path, key, insert_after):
            print(f"  ADDED    {listing['title']}: {readme_path}")
            added.append(readme_path)
    return added

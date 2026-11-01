#!/usr/bin/env python3
"""Generate src/govee_local_api/data/full_scenes.json for given models.

Temporary fork tool. Fetches the full scene library of each SKU from Govee
(all scene types, with parameter blobs) and writes
``{sku: [[name, code, base64 param], ...]}`` in the Govee app's order.
The name is "[Category] Scene Name" in Title Case. An empty param is a
firmware scene.

    uv run python scripts/generate_scene_library.py H805D
"""

import argparse
import json
import sys

from fetch_scene_library import REPO_ROOT, fetch_library

from govee_local_api.light_capabilities import DATA_DIR, SCENE_LIBRARY_FILE

OUTPUT = REPO_ROOT / "src" / "govee_local_api" / DATA_DIR / SCENE_LIBRARY_FILE


def title(text: str) -> str:
    """Title Case: underscores become spaces, and the first letter of each
    word becomes a capital. Other letters stay as they are ("A&M", "LED",
    "Mother's")."""
    words = text.replace("_", " ").split()
    return " ".join(word[:1].upper() + word[1:] for word in words)


def build(sku: str) -> list[list]:
    """All scenes of one model as [[name, code, base64 param], ...].

    A scene with several effects gets the effect name appended. A name that
    is already used gets a number, so no scene is lost.
    """
    data = fetch_library(sku)
    result: list[list] = []
    used: set[str] = set()
    for category in data.get("categories", []):
        prefix = f"[{title(category.get('categoryName', '')) or 'Other'}]"
        for scene in category.get("scenes", []):
            effects = scene.get("lightEffects", [])
            for effect in effects:
                code = effect.get("sceneCode", 0)
                if not code or code > 0xFFFF:
                    continue
                name = scene.get("sceneName", "") or f"Scene {code}"
                if len(effects) > 1 and effect.get("scenceName"):
                    name = f"{name} {effect['scenceName']}"
                name = f"{prefix} {title(name)}"
                base, number = name, 2
                while name.lower() in used:
                    name, number = f"{base} {number}", number + 1
                used.add(name.lower())
                result.append([name, code, effect.get("scenceParam") or ""])
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("skus", nargs="+", metavar="SKU")
    args = parser.parse_args()

    existing = json.loads(OUTPUT.read_text()) if OUTPUT.is_file() else {}
    for sku in args.skus:
        existing[sku] = build(sku)
        blobs = sum(1 for _, _, param in existing[sku] if param)
        print(f"{sku}: {len(existing[sku])} scenes, {blobs} with a blob")
    OUTPUT.write_text(json.dumps(dict(sorted(existing.items())), indent=1) + "\n")
    print(f"Wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

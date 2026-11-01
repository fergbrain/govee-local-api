#!/usr/bin/env python3
"""Generate src/govee_local_api/data/full_scenes.json for given models.

Temporary fork tool. Fetches the full scene library of each SKU from Govee
(all scene types, with parameter blobs) and writes
``{sku: {key: [code, base64 param]}}``. An empty param is a firmware scene.

    uv run python scripts/generate_scene_library.py H805D
"""

import argparse
import json
import sys

from fetch_scene_library import REPO_ROOT, fetch_library, scene_key

from govee_local_api.light_capabilities import DATA_DIR, SCENE_LIBRARY_FILE

OUTPUT = REPO_ROOT / "src" / "govee_local_api" / DATA_DIR / SCENE_LIBRARY_FILE


def build(sku: str) -> dict[str, list]:
    """All scenes of one model as {key: [code, base64 param]}.

    A scene with several effects gets the effect name appended. A key that
    is already used gets a numeric suffix, so no scene is lost.
    """
    data = fetch_library(sku)
    result: dict[str, list] = {}
    for category in data.get("categories", []):
        for scene in category.get("scenes", []):
            effects = scene.get("lightEffects", [])
            for effect in effects:
                code = effect.get("sceneCode", 0)
                if not code or code > 0xFFFF:
                    continue
                name = scene.get("sceneName", "")
                if len(effects) > 1 and effect.get("scenceName"):
                    name = f"{name} {effect['scenceName']}"
                key = scene_key(name) or f"scene_{code}"
                base, n = key, 2
                while key in result:
                    key, n = f"{base}_{n}", n + 1
                result[key] = [code, effect.get("scenceParam") or ""]
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("skus", nargs="+", metavar="SKU")
    args = parser.parse_args()

    existing = json.loads(OUTPUT.read_text()) if OUTPUT.is_file() else {}
    for sku in args.skus:
        existing[sku] = build(sku)
        blobs = sum(1 for _, param in existing[sku].values() if param)
        print(f"{sku}: {len(existing[sku])} scenes, {blobs} with a blob")
    OUTPUT.write_text(json.dumps(dict(sorted(existing.items())), indent=1) + "\n")
    print(f"Wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

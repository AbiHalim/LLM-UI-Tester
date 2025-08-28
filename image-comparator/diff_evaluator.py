import os, json, math, pathlib
from typing import List, Dict
from google import genai
from google.genai import types
from dotenv import load_dotenv

BASE = pathlib.Path("image-comparator/out")
MANIFEST = BASE / "manifest.json"
MODEL = "gemini-2.0-flash-001"  # fast, supports images + JSON schema

def read_bytes(p: pathlib.Path) -> bytes:
    with open(p, "rb") as f:
        return f.read()

def build_schema() -> Dict:
    # Response schema to force strict JSON
    return {
        "type": "OBJECT",
        "required": ["page_summary", "changes"],
        "properties": {
            "page_summary": {"type": "STRING"},
            "changes": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "required": ["id", "type", "severity", "explanation", "risk"],
                    "properties": {
                        "id": {"type": "STRING"},
                        "type": {
                            "type": "STRING",
                            "enum": [
                                "text_change","color_change","layout_shift",
                                "visibility","icon_change","image_change",
                                "new","missing","uncertain"
                            ]
                        },
                        "severity": {"type": "STRING", "enum": ["low","medium","high"]},
                        "before_text": {"type": "STRING"},
                        "after_text": {"type": "STRING"},
                        "explanation": {"type": "STRING"},
                        "risk": {
                            "type": "STRING",
                            "enum": ["usability","accessibility","branding","functional","none"]
                        }
                    }
                }
            }
        }
    }

def chunk(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

def main():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Set GOOGLE_API_KEY env var.")

    manifest = json.load(open(MANIFEST))
    page = manifest["page"]
    changes = manifest["changes"]

    client = genai.Client(api_key=api_key)

    system_instruction = (
        "You are a meticulous UI regression analyst. Compare BEFORE vs AFTER screenshots. "
        "Only describe differences you can SEE. Be precise, avoid speculation. "
        "For each region triptych (left=BEFORE, middle=AFTER, right=HEATMAP), "
        "identify the change and fill the JSON schema exactly."
    )

    # Page thumbnails
    before_img = types.Part.from_bytes(
        data=read_bytes(BASE / page["before_image"]), mime_type="image/png"
    )
    after_img = types.Part.from_bytes(
        data=read_bytes(BASE / page["after_image"]), mime_type="image/png"
    )

    schema = build_schema()

    # Gemini handles multiple images in one request. To be safe with context size,
    # send in batches (e.g., 16 triptychs per call).
    BATCH = 16
    aggregated = {"page_summary": "", "changes": []}

    for batch_i, batch in enumerate(chunk(changes, BATCH), start=1):
        # Build the “contents” for this batch: page context text + page images + manifest slice + triptychs
        region_stub = {
            "viewport": page.get("viewport"),
            "regions": [{"id": c["id"], "bbox": c["bbox"]} for c in batch],
        }

        # Compose parts: brief instruction, page context, page images, then triptychs
        parts: List[types.Part] = [
            "Analyze these regions and return ONLY valid JSON matching the schema.",
            json.dumps(region_stub),
            before_img,
            after_img,
        ]

        # Add triptych images for this batch
        for c in batch:
            p = BASE / c["triptych"]
            parts.append(types.Part.from_bytes(data=read_bytes(p), mime_type="image/png"))

        # Call the model with JSON response enforced
        resp = client.models.generate_content(
            model=MODEL,
            contents=types.UserContent(parts=parts),
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0,
                response_mime_type="application/json",
                response_schema=schema,  # enforce structured output
            ),
        )

        # Parse and merge
        chunk_json = json.loads(resp.text)
        if batch_i == 1:
            aggregated["page_summary"] = chunk_json.get("page_summary", "")
        aggregated["changes"].extend(chunk_json.get("changes", []))

        # Save per-batch (optional, useful for debugging)
        out_path = BASE / f"analysis_batch_{batch_i:02d}.json"
        json.dump(chunk_json, open(out_path, "w"), indent=2)
        print(f"[INFO] Saved {out_path}")

    # Deduplicate by change id (if any overlap across batches)
    seen = set()
    deduped = []
    for ch in aggregated["changes"]:
        if ch["id"] in seen: 
            continue
        seen.add(ch["id"])
        deduped.append(ch)
    aggregated["changes"] = deduped

    final_path = BASE / "analysis_all.json"
    json.dump(aggregated, open(final_path, "w"), indent=2)
    print(f"[INFO] Wrote {final_path}")

if __name__ == "__main__":
    main()

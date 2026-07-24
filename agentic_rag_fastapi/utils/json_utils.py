import json
import re


def extract_json_object(text: str):
    """
    Extract first JSON object or array from model output.

    Tries progressively looser parsing strategies:
    1. Direct JSON parse of the full text.
    2. Strip markdown code fences then re-parse.
    3. Extract the first JSON array via regex.
    4. Extract the first JSON object via regex.

    Raises:
        ValueError: If no valid JSON structure can be extracted.
    """
    text = text.strip()

    # 1. Direct parse
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass

    # 2. Remove markdown fences
    text = text.replace("```json", "").replace("```", "").strip()

    # 3. Try to find a JSON array
    array_match = re.search(r"\[[\s\S]*\]", text)
    if array_match:
        candidate = array_match.group(0)
        try:
            return json.loads(candidate)
        except (json.JSONDecodeError, ValueError):
            pass

    # 4. Try to find a JSON object
    obj_match = re.search(r"\{[\s\S]*\}", text)
    if obj_match:
        candidate = obj_match.group(0)
        try:
            return json.loads(candidate)
        except (json.JSONDecodeError, ValueError):
            pass

    raise ValueError("Could not extract valid JSON from model output.")

import json
import re

def extract_json_object(text: str):
    """
    Extract first JSON object or array from model output.
    """
    text = text.strip()

    # direct parse
    try:
        return json.loads(text)
    except:
        pass

    # remove markdown fences
    text = text.replace("```json", "").replace("```", "").strip()

    # try array
    array_match = re.search(r"\[[\s\S]*\]", text)
    if array_match:
        candidate = array_match.group(0)
        try:
            return json.loads(candidate)
        except:
            pass

    # try object
    obj_match = re.search(r"\{[\s\S]*\}", text)
    if obj_match:
        candidate = obj_match.group(0)
        try:
            return json.loads(candidate)
        except:
            pass

    raise ValueError("Could not extract valid JSON from model output.")

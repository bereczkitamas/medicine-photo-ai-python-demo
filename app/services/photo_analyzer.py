import os
from typing import Optional, Tuple

try:
    import google.generativeai as genai
except Exception:  # pragma: no cover
    genai = None  # type: ignore


class PackagePhotoAnalyzer:
    """Thin wrapper around Google Gemini for vision analysis.

    Responsibilities:
    - Decide if the image is a valid medicine package photo.
    - Extract medicine name, form and active substance from the package text.

    It uses environment variable GOOGLE_API_KEY. If not configured or the
    google.generativeai package is missing, it falls back to a no-op mode
    where it returns (None, None, None) meaning unknown.
    """

    def __init__(self, model_name: str = os.environ.get('GEMINI_MODEL', 'gemini-1.5-flash')):
        self.model_name = model_name
        self.api_key = os.environ.get('GOOGLE_API_KEY')
        self._enabled = bool(self.api_key) and genai is not None
        if self._enabled:
            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel(self.model_name)
        else:
            self._model = None

    def analyze_image(self, image_bytes: bytes, mime_type: str) -> Tuple[Optional[bool], Optional[str], Optional[str], Optional[str]]:
        """Return tuple: (is_valid_package, medicine_name, form, substance)

        - is_valid_package: True/False if the model can decide; None if unknown
        - medicine_name/form/substance: strings if detected; otherwise None
        """
        if not self._enabled:
            return None, None, None, None

        prompt = (
            "You are an expert pharmacist assistant. You will receive a single photo.\n"
            "Task 1: Decide if the photo clearly shows a medicine package or blister/box (not a leaflet alone, not a person, not random object).\n"
            "Respond with yes or no.\n"
            "Task 2: If it is a medicine package, read printed information and extract: \n"
            "- medicine name (brand or generic as printed),\n"
            "- form (e.g., tablet, capsule, syrup, injection, cream, gel, drops),\n"
            "- active substance (main active ingredient).\n"
            "If any of these are not present, say unknown for that field.\n"
            "Return your answer strictly as JSON with keys: {\"is_valid\": boolean, \"medicine_name\": string|null, \"form\": string|null, \"substance\": string|null}.\n"
        )

        img_part = {"mime_type": mime_type, "data": image_bytes}
        try:
            resp = self._model.generate_content([prompt, img_part])  # type: ignore
            text = resp.text if hasattr(resp, 'text') else str(resp)
        except Exception:
            return None, None, None, None

        # Attempt to parse JSON
        import json
        try:
            # Extract JSON object from response text if surrounded by extra text
            start = text.find('{')
            end = text.rfind('}')
            payload = text[start:end + 1] if start != -1 and end != -1 else text
            data = json.loads(payload)

            is_valid = data.get('is_valid')
            medicine_name = data.get('medicine_name')
            form = data.get('form')
            substance = data.get('substance')

            # Normalize empty/unknown strings
            def norm(v):
                if v is None:
                    return None
                s = str(v).strip()
                return None if not s or s.lower() in {"n/a", "unknown", "none"} else s

            return (bool(is_valid) if isinstance(is_valid, bool) else None,
                    norm(medicine_name), norm(form), norm(substance))
        except Exception:
            return None, None, None, None

import os
import logging
from typing import Optional, Tuple

try:
    from google import genai
    from google.genai import types
except Exception:  # pragma: no cover
    genai = None  # type: ignore

logger = logging.getLogger(__name__)

class PackagePhotoAnalyzer:
    """Thin wrapper around Google Gemini for vision analysis.

    Responsibilities:
    - Decide if the image is a valid medicine package photo.
    - Extract medicine name, form and active substance from the package text.

    It uses environment variable GOOGLE_API_KEY. If not configured or the
    google-genai package is missing, it falls back to a no-op mode
    where it returns (None, None, None) meaning unknown.
    """

    def __init__(self, model_name: str = os.environ.get('GEMINI_MODEL', 'gemini-1.5-flash')):
        self.model_name = model_name
        self.api_key = os.environ.get('GOOGLE_API_KEY')
        self._enabled = bool(self.api_key) and genai is not None
        if self._enabled:
            # Initialize google-genai client
            logger.info("Initializing Google GenAI client with model=%s", self.model_name)
            self._client = genai.Client(api_key=self.api_key)
        else:
            logger.warning("PackagePhotoAnalyzer disabled: GOOGLE_API_KEY missing or google-genai not installed")
            self._client = None

    def __del__(self):
        if self._client:
            self._client.close()

    def analyze_image(self, image_bytes: bytes, mime_type: str) -> Tuple[Optional[bool], Optional[str], Optional[str], Optional[str]]:
        """Return tuple: (is_valid_package, medicine_name, form, substance)

        - is_valid_package: True/False if the model can decide; None if unknown
        - medicine_name/form/substance: strings if detected; otherwise None
        """
        if not self._enabled:
            logger.debug("analyze_image skipped: analyzer disabled")
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

        try:
            # Prepare image part for google-genai
            logger.debug("Calling GenAI generate_content with model=%s, mime=%s, size=%d", self.model_name, mime_type, len(image_bytes))
            resp = self._client.models.generate_content(model=self.model_name, contents=[
                prompt,
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type)])
            text = resp.text if hasattr(resp, 'text') else str(resp)
            logger.debug("GenAI raw response text length=%d", len(text) if text else 0)
        except Exception as e:
            logger.exception("Error in analyze_image: %s", e)
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
        except Exception as e:
            logger.warning("Failed to parse GenAI JSON response: %s; text=%s", e, (text[:300] + '...') if text and len(text) > 300 else text)
            return None, None, None, None

from langdetect import DetectorFactory, detect

DetectorFactory.seed = 0
SUPPORTED = {"en": "English", "kn": "Kannada", "hi": "Hindi", "te": "Telugu"}


def resolve_language(text: str, requested: str | None) -> str:
    if requested and requested != "Auto":
        return requested
    try:
        return SUPPORTED.get(detect(text), "English")
    except Exception:
        return "English"

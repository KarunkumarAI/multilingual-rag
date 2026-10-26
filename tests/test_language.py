from backend.app.core.language import resolve_language


def test_manual_english():
    assert resolve_language("Hello", "English") == "English"


def test_manual_kannada():
    assert resolve_language("ನಮಸ್ಕಾರ", "Kannada") == "Kannada"


def test_manual_hindi():
    assert resolve_language("नमस्ते", "Hindi") == "Hindi"


def test_manual_telugu():
    assert resolve_language("నమస్కారం", "Telugu") == "Telugu"


def test_auto_english():
    assert resolve_language(
        "This is a simple English sentence for language detection.",
        "Auto",
    ) == "English"


def test_empty_text_falls_back_to_english():
    assert resolve_language("", "Auto") == "English"
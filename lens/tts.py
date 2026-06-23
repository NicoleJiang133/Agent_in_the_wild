"""Text-to-speech — NeuTTS on Pi, pyttsx3 as fallback."""

try:
    from neutts import NeuTTS
    _tts = NeuTTS()

    def speak(text: str) -> None:
        _tts.synthesize(text, play=True)

except ImportError:
    try:
        import pyttsx3
        _engine = pyttsx3.init()
        _engine.setProperty("rate", 165)

        def speak(text: str) -> None:
            _engine.say(text)
            _engine.runAndWait()

    except Exception:
        def speak(text: str) -> None:
            print(f"[TTS] {text}")

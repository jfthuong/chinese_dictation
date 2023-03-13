"""Classes and functions to select characters to practice dictation"""
import enum
import re
from dataclasses import dataclass
from pathlib import Path
from random import choice
from typing import Optional, Union

import pyttsx3
import streamlit as st
from pydub.audio_segment import AudioSegment
from pypinyin import Style, lazy_pinyin
from pyttsx3.voice import Voice

from temp_filename import temporary_filename


class Status(enum.Enum):
    """Status of a dictation"""

    UNKNOWN = "❔"
    MISSING = "🈳"
    INCORRECT = "❌"
    CORRECT = "✅"

    @classmethod
    def from_string(cls, value: Optional[str]) -> "Status":
        """Convert a string to a Status"""
        if value is None:
            return cls.UNKNOWN

        for status in cls:
            if status.value == value:
                return status

        raise ValueError(f"Unknown status {value}")

    @classmethod
    def list_values(cls) -> list[str]:
        """List all values"""
        return [s.value for s in cls]

    @classmethod
    def get_help(cls) -> str:
        """Get a help message"""
        return ", ".join(f"{s.value}: {s.name}" for s in cls)


@st.cache_data
def get_chinese_voice() -> Voice:
    """Get a voice for Chinese"""
    engine = pyttsx3.init()
    voices = engine.getProperty("voices")
    for voice in voices:
        if voice.languages and voice.languages[0] == "zh-CN":
            return voice
        if "Chinese" in voice.name or "Mandarin" in voice.name.title():
            return voice

    raise RuntimeError(f"No Chinese voice found among {voices}")


CHINESE_VOICE = get_chinese_voice()


@dataclass
class Character:
    """A word with pinyin and translation"""

    chars: str
    _status: Status = Status.UNKNOWN

    def _generate_sound(self, voice_rate: int, path: Path):
        """Generate a sound file for Chinese Characters"""
        engine = pyttsx3.init()
        engine.setProperty("voice", CHINESE_VOICE.id)
        engine.setProperty("rate", voice_rate)

        # to prevent "already in loop"
        engine._inLoop = False  # pylint: disable=protected-access

        # engine.stop()
        engine.save_to_file(self.chars, str(path))
        engine.runAndWait()

    @st.cache_data
    def generate_mp3(self, voice_rate: int) -> bytes:
        """Generate a MP3 for Chinese Characters"""
        with temporary_filename(suffix=".mp3") as mp3_path:
            self._generate_sound(voice_rate, mp3_path)
            return mp3_path.read_bytes()

    @st.cache_data
    def generate_audio_segment(self, voice_rate: int) -> AudioSegment:
        """Generate an audio file for Chinese Characters"""
        with temporary_filename(suffix=".wav") as wav_path:
            self._generate_sound(voice_rate, wav_path)
            return AudioSegment.from_wav(wav_path)

    @property
    def pinyin(self) -> str:
        """Pinyin representation"""
        return " ".join(lazy_pinyin(self.chars, style=Style.TONE))

    @property
    def status(self) -> str:
        """Status of the character"""
        return self._status.name

    @status.setter
    def status(self, value: Union[Status, str, None]):
        self._status = value if isinstance(value, Status) else Status.from_string(value)

    def __hash__(self) -> int:
        return hash(self.chars)

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, Character):
            return False

        return self.chars == __o.chars


@st.cache_data
def next_character(char_list: set[str]) -> Character:
    """Select a random character from a list"""
    undone_chars = char_list - {c.chars for c in st.session_state.characters_done}

    if len(undone_chars) == 1:
        st.balloons()

    elif len(undone_chars) == 0:
        st.snow()
        undone_chars = char_list

    char = choice(list(undone_chars))

    return Character(char)


def split_characters(text: Optional[str]) -> list[str]:
    """Split a string of characters"""
    if not text:
        return []

    patt_sep = re.compile(r"\s*[,，]\s*|\s+")
    return [c.strip() for c in patt_sep.split(text) if c.strip()]


def select_characters() -> set[str]:
    """Select list of characters"""
    selection = st.sidebar.radio(
        "Selection mode", ["From File", "From List", "Few Characters"]
    )
    list_characters = ""
    help_ = "Separate characters with space, comma or newline"

    if selection == "From File":
        uploaded_file = st.sidebar.file_uploader("File", type=["txt"], help=help_)
        if uploaded_file:
            list_characters = uploaded_file.read().decode("utf-8")

    elif selection == "From List":
        list_characters = st.sidebar.text_area(
            "Characters", "默写 联系", height=300, help=help_
        )

    elif selection == "Few Characters":
        list_characters = st.sidebar.text_input("Character", "", help=help_)

    else:
        raise RuntimeError(f"Unknown selection {selection}")

    return set(split_characters(list_characters))


def generate_dictation(
    characters: list[Character], voice_rate: int, repetition=2, silence=1_000
) -> bytes:
    """Generate dictation from a list of characters

    Args:
        characters: List of characters
        voice_rate: Voice rate
        repetition: Number of repetition. Defaults to 2.
        silence: Silence between repetitions in ms. Defaults to 1_000.
    """
    if not characters:
        return b""

    silence_segment = AudioSegment.silent(duration=silence)

    audio = AudioSegment.empty()
    for char in characters:
        for _ in range(repetition):
            audio += char.generate_audio_segment(voice_rate)
            audio += silence_segment
        audio += silence_segment * len(char.chars)

    with temporary_filename(suffix=".mp3") as mp3_path:
        audio.export(mp3_path, format="mp3")
        return mp3_path.read_bytes()

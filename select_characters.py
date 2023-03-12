import enum
import random
import re
from dataclasses import dataclass
from itertools import chain
from random import choice
from typing import Optional, Union


import pyttsx3
import streamlit as st
from pyttsx3.voice import Voice
from pypinyin import pinyin

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

    @st.cache_data
    def generate_mp3(self, voice_rate: int) -> bytes:
        """Generate a MP3 for Chinese Characters"""
        with temporary_filename(suffix=".mp3") as mp3_path:
            engine = pyttsx3.init()
            engine.setProperty("voice", CHINESE_VOICE.id)
            engine.setProperty("rate", voice_rate)

            # to prevent "already in loop"
            engine._inLoop = False  # pylint: disable=protected-access

            # engine.stop()
            engine.save_to_file(self.chars, str(mp3_path))
            engine.runAndWait()

            return mp3_path.read_bytes()

    @property
    def pinyin(self) -> str:
        """Pinyin representation"""
        return " ".join(chain.from_iterable(pinyin(self.chars)))

    @property
    def status(self) -> str:
        """Status of the character"""
        return self._status.name

    @status.setter
    def status(self, value: Union[Status, str, None]):
        self._status = value if isinstance(value, Status) else Status.from_string(value)


@st.cache_data
def next_character(char_list: set[str]) -> Character:
    """Select a random character from a list"""
    return Character(choice(list(char_list)))


def split_characters(text: Optional[str]) -> set[str]:
    """Split a string of characters"""
    if not text:
        return set()

    patt_sep = re.compile(r"\s*[,，]\s*|\s+")
    return {c.strip() for c in patt_sep.split(text) if c.strip()}


def select_characters(shuffle: bool = True) -> set[str]:
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

    characters = split_characters(list_characters)
    if characters and shuffle:
        characters_as_list = list(characters)
        random.shuffle(characters_as_list)
        characters = set(characters_as_list)

    return characters

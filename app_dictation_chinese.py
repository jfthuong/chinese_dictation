import enum
import logging
import re
from dataclasses import dataclass
from itertools import chain
from random import choice
from typing import Optional


import pyttsx3
import streamlit as st
from pyttsx3.voice import Voice
from pypinyin import pinyin

from temp_filename import temporary_filename

st.set_page_config(layout="wide", page_title="默写练习", page_icon="📝")
st.title("默写练习 - Chinese Dictation")

logging.basicConfig(
    filename="diction.log", level=logging.INFO, format="%(asctime)s %(message)s"
)


class Status(enum.Enum):
    """Status of a dictation"""

    UNKNOWN = "❔"
    UNANSWERED = "🈳"
    INCORRECT = "❌"
    CORRECT = "✅"

    @classmethod
    def from_string(cls, value: Optional[str]) -> "Status":
        """Convert a string to a Status"""
        if value == "❔" or value is None:
            return cls.UNKNOWN
        if value == "🈳":
            return cls.UNANSWERED
        if value == "❌":
            return cls.INCORRECT
        if value == "✅":
            return cls.CORRECT
        raise ValueError(f"Unknown status {value}")

    @classmethod
    def list_values(cls) -> list[str]:
        """List all values"""
        return [s.value for s in cls]

    @classmethod
    def get_help(cls) -> str:
        """Get a help message"""
        return ", ".join(f"{s.value}: {s.name}" for s in cls)


@dataclass
class Word:
    """A word with pinyin and translation"""

    characters: str
    status: Optional[Status] = None

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
            engine.save_to_file(self.characters, str(mp3_path))
            engine.runAndWait()

            return mp3_path.read_bytes()

    @property
    def pinyin(self) -> str:
        """Pinyin representation"""
        return " ".join(chain.from_iterable(pinyin(self.characters)))


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


@st.cache_data
def select_character(char_list: set[str]) -> Word:
    """Select a random character from a list"""
    return Word(choice(list(char_list)))


ORIGINAL_RATE = 100

st.sidebar.header("Settings")
characters_list = st.sidebar.text_area(
    "Characters", "好", help="Separate characters with space, comma or newline"
)
use_specific_characters = st.sidebar.checkbox("Use specific characters", False)
if use_specific_characters:
    characters_list = st.sidebar.text_input("Character", "")

patt_sep = re.compile(r"\s*[,，]\s*|\s+")
list_characters = {c.strip() for c in patt_sep.split(characters_list) if c.strip()}

if "characters_done" not in st.session_state:
    st.session_state.characters_done = []
characters_done = st.session_state.characters_done


def record_characters(characters: Word):
    """Add characters to the list of characters done"""
    if not st.session_state.characters_done:
        st.session_state.characters_done = [characters]
    elif characters.characters != st.session_state.characters_done[-1].characters:
        st.session_state.characters_done.append(characters)


tab_practice, tab_review = st.tabs(["Practice", "Review"])

with tab_practice:
    st.header("Dictation")
    st.metric("Number of characters done", len(characters_done))

    rate = st.slider("Speed (words per minute)", 50, 200, ORIGINAL_RATE)
    word = select_character(list_characters)
    record_characters(word)

    audio_zone = st.empty()

    if st.button("⏭️ Next"):
        st.cache_data.clear()
        word = select_character(list_characters)
        record_characters(word)

    mp3 = word.generate_mp3(rate)
    audio_zone.audio(mp3)

    st.header("Solution")
    with st.expander("Show solution"):
        st.subheader(f"{word.characters}")
        st.subheader(f"{word.pinyin}")


with tab_review:
    st.header("Review")
    if st.button("🧹Clear list of characters"):
        characters_done.clear()

    if characters_done:
        st.write(f"Caption for status: {Status.get_help()}")
        for i, word in enumerate(characters_done):
            col_w, col_p, col_s = st.columns(3)
            col_w.subheader(f"{word.characters}")
            col_p.write(f"{word.pinyin}")
            status = col_s.radio(
                "status",
                Status.list_values(),
                key=f"check_{i}",
                horizontal=True,
                label_visibility="collapsed",
            )
            word.status = Status.from_string(status)
    else:
        st.header("No characters done yet")

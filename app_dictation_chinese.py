import codecs
import csv
from datetime import datetime
import logging
from pathlib import Path

import streamlit as st

# Following line has to be before the import because the code uses streamlit
st.set_page_config(layout="wide", page_title="默写练习", page_icon="📝")

from select_characters import Character, Status, next_character, select_characters


st.title("默写练习 - Chinese Dictation")

logging.basicConfig(
    filename="diction.log", level=logging.INFO, format="%(asctime)s %(message)s"
)


ORIGINAL_RATE = 100

st.sidebar.header("Settings")

list_characters = select_characters()
if not list_characters:
    st.error("No characters selected")
    st.stop()


if "characters_done" not in st.session_state:
    st.session_state.characters_done = []
characters_done = st.session_state.characters_done


def record_characters(characters: Character):
    """Add characters to the list of characters done"""
    if not st.session_state.characters_done:
        st.session_state.characters_done = [characters]
    elif characters.chars != st.session_state.characters_done[-1].chars:
        st.session_state.characters_done.append(characters)


tab_practice, tab_review = st.tabs(["Practice", "Review"])

with tab_practice:
    st.header("Dictation")
    st.metric("Number of characters done", len(characters_done))

    rate = st.slider("Speed (words per minute)", 50, 200, ORIGINAL_RATE)
    word = next_character(list_characters)
    record_characters(word)

    audio_zone = st.empty()

    if st.button("⏭️ Next"):
        st.cache_data.clear()
        word = next_character(list_characters)
        record_characters(word)

    mp3 = word.generate_mp3(rate)
    audio_zone.audio(mp3)

    st.header("Solution")
    with st.expander("Show solution"):
        st.subheader(f"{word.chars}")
        st.subheader(f"{word.pinyin}")


def generate_report(csv_path: Path):
    """Generate a report"""
    need_header = not csv_path.exists()

    # We need to add BOM for UTF-8 to be able to open in Excel
    if need_header:
        with csv_path.open("wb") as f:
            f.write(codecs.BOM_UTF8)

    with csv_path.open("a", newline="", encoding="utf-8") as f:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        writer = csv.writer(f, dialect="excel")

        if need_header:
            header = "Date Character Pinyin Status".split()
            writer.writerow(header)

        writer.writerows([now, c.chars, c.pinyin, c.status] for c in characters_done)

    st.success(f"Report updated in {csv_path}")


with tab_review:
    st.header("Review")
    if st.button("🧹Clear list of characters"):
        for word in characters_done:
            st.write(f" * {word.chars} - {word.status}")
        # characters_done.clear()
        generate_report(Path("dictation_report.csv"))

    if characters_done:
        st.write(f"Caption for status: {Status.get_help()}")
        for i, word in enumerate(characters_done):
            col_w, col_p, col_s = st.columns(3)
            col_w.subheader(word.chars)
            col_p.write(word.pinyin)
            word.status = col_s.radio(  # type: ignore  # None supported
                "status",
                Status.list_values(),
                key=f"check_{i}",
                horizontal=True,
                label_visibility="collapsed",
            )
    else:
        st.header("No characters done yet")

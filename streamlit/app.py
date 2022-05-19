import json
import os
import random

import streamlit as st
from utils import extract_keyword, extract_text, generate_quiz

st.header("Did you read the paper?".title())

NUM_OF_QUESTION = 10
if "prepared" not in st.session_state:
    st.session_state["prepared"] = False
if "choice" not in st.session_state:
    st.session_state["choice"] = []
if "questions" not in st.session_state:
    st.session_state["questions"] = []


def disable_question(question_id, option_id):
    st.session_state["questions"][question_id]["disabled"] = True
    option, checked = st.session_state["questions"][question_id]["options"][
        option_id
    ]
    st.session_state["questions"][question_id]["options"][option_id] = (
        option,
        True,
    )
    answer = st.session_state["questions"][question_id]["answer"]
    st.session_state["choice"].append(option == answer)


def reset():
    st.session_state["prepared"] = False
    st.session_state["choice"] = []
    st.session_state["questions"] = []


placeholder = st.empty()

if not st.session_state["prepared"]:
    uploaded_file = placeholder.file_uploader("PDF")
    if uploaded_file is not None:

        file_path = os.path.join("pdfs", uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        with st.spinner("Extracting text from pdf..."):
            text = extract_text(file_path)
        with st.spinner("Extracting keywords from text..."):
            keywords = extract_keyword(text)
        with st.spinner("Generating quiz ...."):
            generate_quiz(file_path, keywords)
        with open("quiz_data.json") as f:
            data = json.load(f)

        st.session_state["questions"] = random.sample(data, NUM_OF_QUESTION)
        for index, question in enumerate(st.session_state["questions"]):

            question["disabled"] = False
            options = random.sample(
                question["options"], len(question["options"])
            )
            option_list = []
            for opt_idx, option in enumerate(options):
                option_list.append((option, False))

            question["options"] = option_list
        st.session_state["prepared"] = True
        placeholder.empty()


if len(st.session_state["choice"]) < NUM_OF_QUESTION:
    for index, question in enumerate(st.session_state["questions"]):
        st.text("{}. Choose the best answer.".format(index + 1))
        st.image(question["masked_image"])
        for opt_idx, (option, checked) in enumerate(question["options"]):
            st.checkbox(
                option.lower(),
                value=checked,
                key=question["masked_image"] + option,
                disabled=st.session_state["questions"][index]["disabled"],
                on_change=disable_question,
                args=(
                    index,
                    opt_idx,
                ),
            )
else:
    punc = "." * (NUM_OF_QUESTION - sum(st.session_state["choice"]))
    st.subheader(
        "{} / {} {}".format(
            sum(st.session_state["choice"]), NUM_OF_QUESTION, punc
        )
    )
    st.button("Retry", on_click=reset)

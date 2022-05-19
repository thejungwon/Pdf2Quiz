import json
import math
import random
import uuid

import cv2
import gensim.downloader
import numpy as np
import pandas as pd
import pytesseract
import spacy
from pdf2image import convert_from_path
from pytesseract import Output
from sklearn.feature_extraction.text import TfidfVectorizer

import streamlit as st


@st.cache(allow_output_mutation=True)
def get_spacy_model():
    return spacy.load("en_core_web_sm")  # Load the English Model


@st.cache(allow_output_mutation=True)
def get_word_embedding():
    return gensim.downloader.load("glove-wiki-gigaword-50")


nlp = get_spacy_model()
word_embedding = get_word_embedding()


def extract_text(pdf_name):
    images = convert_from_path(pdf_name)

    meaningful_text = []

    for image in images:
        meaningless_blocks = []
        image = np.array(image)
        h, w, _ = image.shape

        h = int((h * 1000) / w)
        image = cv2.resize(image, (1000, h))
        d = pytesseract.image_to_data(
            image,
            lang="eng",
            output_type=Output.DICT,
        )

        n_boxes = len(d["level"])

        for i in range(n_boxes):
            if d["level"][i] == 3:
                if d["width"][i] < d["height"][i]:
                    meaningless_blocks.append(d["block_num"][i])
                (x, y, w, h) = (
                    d["left"][i],
                    d["top"][i],
                    d["width"][i],
                    d["height"][i],
                )
                cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

        df = pd.DataFrame(d)
        df = df[~df["block_num"].isin(meaningless_blocks)]

        df = df[pd.to_numeric(df["conf"]) > 50]
        text_blocks = (
            df.groupby("block_num")["text"]
            .transform(lambda x: " ".join(x))
            .drop_duplicates()
        )
        for block in text_blocks:
            if len(block.split()) > 2:
                meaningful_text.append(block)

    return meaningful_text


def extract_keyword(meaningful_text):
    def spacy_tokenizer(document):
        tokens = nlp(document)
        tokens = [
            token.lemma_
            for token in tokens
            if (
                token.is_stop == False
                and token.pos_ in ["NOUN", "PROPN"]
                and str(token).isalnum()
                and token.is_punct == False
                and token.lemma_.strip() != ""
            )
        ]
        return tokens

    for i, text in enumerate(meaningful_text):
        meaningful_text[i] = meaningful_text[i].strip()
        meaningful_text[i] = meaningful_text[i].replace("  ", " ")
        meaningful_text[i] = meaningful_text[i].replace("‘", "")

    all_sents = []
    for text in meaningful_text:
        doc = nlp(text)
        for sent in doc.sents:

            all_sents.append(str(sent))

    tfidf_vectorizer = TfidfVectorizer(
        tokenizer=spacy_tokenizer, max_df=0.7, min_df=0.01
    )
    result = tfidf_vectorizer.fit_transform(all_sents)

    dense = result.todense()
    denselist = dense.tolist()
    df = pd.DataFrame(denselist, columns=tfidf_vectorizer.get_feature_names())

    columns = df.columns

    def re_score(score, weight):
        return score * (1 + math.log(weight))

    for col in columns:
        df[col] = df[col].apply(re_score, weight=len(col))

    answers = df.sum().sort_values(ascending=False)[:20]
    return answers


def generate_quiz(pdf_name, answers):

    questions = []

    def lemm(text):

        if not text:
            return ""
        if text.upper() == text.lower():
            return ""
        tokens = nlp(text)

        return "".join([token.lemma_ for token in tokens])

    images = convert_from_path(pdf_name)

    for image in images:
        print("here")
        image = np.array(image)
        h, w, _ = image.shape

        h = int((h * 1000) / w)
        image = cv2.resize(image, (1000, h))
        d = pytesseract.image_to_data(
            image,
            lang="eng",
            output_type=Output.DICT,
        )
        ocr_df = pd.DataFrame(d)
        for answer in answers.keys():
            print(answer)
            try:
                all_sims = word_embedding.most_similar(answer, topn=50)
            except Exception as e:
                print(e)
                continue
            len2word = {}
            for word, sim in sorted(all_sims, key=lambda x: len(x[0])):
                if word.encode().isalpha() and not word.lower().startswith(
                    answer.lower()
                ):
                    if len(word) in len2word:
                        len2word[len(word)].append(word)
                    else:
                        len2word[len(word)] = [word]
            answer_len = len(answer)
            incorrect = []
            try:
                for length in range(answer_len - 1, answer_len + 1):
                    incorrect += len2word.get(length, [])
                other_options = random.sample(incorrect, 3)
            except:
                options = [word for word, _ in all_sims]
                other_options = random.sample(options, 3)

            targets = ocr_df[ocr_df["text"].apply(lemm) == answer]

            for _, target in targets.iterrows():
                image1 = image.copy()
                image2 = image.copy()
                original_image_name = "images/{}.png".format(uuid.uuid4().hex)
                masked_image_name = "images/{}.png".format(uuid.uuid4().hex)

                (x, y, w, h) = (
                    target["left"],
                    target["top"],
                    target["width"],
                    target["height"],
                )
                cv2.rectangle(
                    image2,
                    (x - 2, y - 2),
                    (x + w + 2, y + h + 2),
                    (0, 0, 255),
                    -2,
                )
                cv2.rectangle(
                    image1,
                    (x - 2, y - 2),
                    (x + w + 2, y + h + 2),
                    (0, 0, 255),
                    2,
                )
                box = ocr_df[ocr_df["block_num"] == target["block_num"]].iloc[0]
                (x, y, w, h) = (
                    box["left"],
                    box["top"],
                    box["width"],
                    box["height"],
                )

                original_image = image1[y : y + h, x : x + w]
                masked_image = image2[y : y + h, x : x + w]
                cv2.imwrite(original_image_name, original_image)
                cv2.imwrite(masked_image_name, masked_image)

                question = {
                    "answer": answer,
                    "options": [answer] + other_options,
                    "masked_image": masked_image_name,
                    "original_image": original_image_name,
                }
                questions.append(question)

    with open("quiz_data.json", "w") as f:
        json.dump(questions, f)

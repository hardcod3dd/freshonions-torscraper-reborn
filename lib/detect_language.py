# -- coding: utf-8 --
# encoding=utf8
from langdetect import detect_langs
from tor_db import *
import sys
import importlib
import pycountry
import logging


def classify(text, debug=False):
    # identifier.set_languages(DETECT_LANGUAGES)
    try:
        lang1 = detect_langs(text)[0]
    except UnicodeDecodeError:
        lang1 = detect_langs(text.decode("utf-8"))[0]
    prob = lang1.prob
    lang = lang1.lang

    if debug:
        return (lang, prob)

    if prob > 0.90:
        return lang

    return None


def code_to_lang(code):
    logging.info("performing code_to_lang({})".format(code))
    lang = pycountry.languages.get(alpha_2=code)
    if not lang:
        return None
    return lang.name

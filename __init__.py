import os
import sys
libs_path = os.path.join(os.path.dirname(__file__), "libs")  # libs フォルダ
if libs_path not in sys.path:
    sys.path.insert(0, libs_path)

import cv2
import pytesseract
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import spacy
from deep_translator import GoogleTranslator
from aqt import mw
from aqt.utils import showInfo
from aqt.qt import *
from anki.notes import Note
import requests
from PIL import Image
import numpy as np

def getImage():
    # QFileDialog を作成
    file_dialog = QFileDialog()
    file_dialog.setNameFilter("画像ファイル (*.png *.jpg *.jpeg *.bmp *.gif)")
    file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)

    if file_dialog.exec():
        file_path = file_dialog.selectedFiles()[0]
        # Pillow で画像を開く
        img_pil = Image.open(file_path)
        # PillowからOpenCVに変換
        img_opencv = np.array(img_pil)
        return img_opencv

def setWords(img):
    config_custom = r'--psm 6'
    data_row = pytesseract.image_to_string(img,lang='eng',config=config_custom)
    #訂正
    data = ' '.join(data_row.splitlines())
    text_detected = data.replace("|", "I")
    # 初回だけ必要
    #nltk.download('stopwords')

    #自然言語処理
    nlp = spacy.load("en_core_web_sm")
    #ストップワード
    stop_words = set(stopwords.words('english'))

    #トークン化(どちらかを使う)
    text_token = nlp(text_detected) #SpaCy
    #text_token = word_tokenize(text_detected) #NLTK

    words_processed = []
    for token in text_token:
        # トークンがアルファベットだけで構成されているか（数字や記号は除外）
        if not token.is_alpha:
            continue
        # レンマ化した単語を小文字に変換
        lemma = token.lemma_.lower()
        # ストップワードでないか確認
        if lemma in stop_words:
            continue
        # 条件を満たした単語だけリストに追加
        words_processed.append(lemma)


    # 重複排除
    words = list(set(words_processed))

    # 翻訳器の準備（英語→日本語）
    translator = GoogleTranslator(source='en', target='ja')

    #翻訳
    dictionary = [0]*len(words)

    for i in range(len(words)):
        try:
            dictionary[i] = [words[i],translator.translate(words[i])]
        except Exception as e:
            dictionary[i] = f"翻訳エラー: {e}"

    return dictionary

def makeNote(deck_name,dic):
    deck_id = mw.col.decks.id(deck_name)
    model = mw.col.models.by_name("基本")

    if not model:
        showInfo("ノートタイプ '基本' が見つかりません")
        return
    mw.col.models.set_current(model)

    for combi in dic:
        word = combi[0]
        meaning = combi[1]

        # 新しいノートを作成
        note = Note(mw.col, model)
        note.did = deck_id
        note.fields[0] = word          # 表面（Front）
        note.fields[1] = meaning       # 裏面（Back）
        
        mw.col.add_note(note,deck_id)
        mw.reset()

def getNoteName():
    text, ok = QInputDialog.getText(None, "デッキ名を決めてください", "")
    failed_text = "デッキ"
    if ok:
        return text
    else :
        return failed_text

def testFunction():
    img = getImage()
    note_name = getNoteName()
    words = setWords(img)
    makeNote(note_name, words)

# 新しいメニュー項目 "test" を作成
action = QAction("jijiron", mw)
# この項目をクリックしたらtestFunctionを呼び出す
action.triggered.connect(testFunction)
# ツールメニューに反映
mw.form.menuTools.addAction(action)
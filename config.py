import os


class Config:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")

    RAW_DATA_PATH = os.path.join(DATA_DIR, "finally.csv")
    LABEL_MAP_PATH = os.path.join(DATA_DIR, "label_map.json")

    TRAIN_TXT = os.path.join(BASE_DIR, "fasttext_train.txt")
    VAL_TXT = os.path.join(BASE_DIR, "fasttext_val.txt")
    MODEL_PATH = os.path.join(BASE_DIR, "bio_fasttext_model.bin")

    TEST_SIZE = 0.2
    RANDOM_SEED = 42

    LR = 0.3
    EPOCH = 200
    WORD_NGRAMS = 2
    LOSS_FUNC = "ova"
    DIM = 100

    DEFAULT_THRESHOLD = 0.2

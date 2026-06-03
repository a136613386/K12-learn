# config.py
import os


class Config:
    # ---------------- 路径配置 ----------------
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # 输入的原始数据与映射表
    RAW_JSON_DATA = os.path.join(BASE_DIR, "./data/bio_train_data_answer_500.json")
    LABEL_MAP_PATH = os.path.join(BASE_DIR, "./data/label_map.json")

    # 中间生成的 FastText 文本格式路径
    TRAIN_TXT = os.path.join(BASE_DIR, "fasttext_train.txt")
    VAL_TXT = os.path.join(BASE_DIR, "fasttext_val.txt")

    # 模型保存路径
    MODEL_PATH = os.path.join(BASE_DIR, "bio_fasttext_model.bin")

    # ---------------- 模型超参数 ----------------
    TEST_SIZE = 0.2  # 验证集比例 (20%拿来做测试)
    RANDOM_SEED = 42  # 随机种子

    LR = 0.2  # 学习率
    EPOCH = 200  # 训练轮数
    WORD_NGRAMS = 2  # 词组特征（2-Gram）
    LOSS_FUNC = 'ova'  # 多标签核心：One-Vs-All
    DIM = 100  # 词向量维度

    # ---------------- 推理配置 ----------------
    DEFAULT_THRESHOLD = 0.1  # 默认的预测概率阈值
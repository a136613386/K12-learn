import torch
from torch.utils.data import Dataset, DataLoader
from transformers import BertTokenizer
from tqdm import tqdm
import time
from datetime import timedelta
from config import Config
import time
conf=Config()
def load_raw_data(file_path):
    """
    读取原始数据文件，解析为文本和标签。
    参数：
        file_path (str): 数据文件路径（如dev2.txt）。
    返回：
        List[Tuple[str, int]]: 包含(文本, 标签)的列表。
    """
    data = []
    with open(file_path, "r", encoding="UTF-8") as f:
        for line in tqdm(f, desc="Loading data"):
            line = line.strip()
            if not line:
                continue
            text, label = line.split("\t")
            data.append((text, int(label)))
    print(data[:5])
    return data

class TextDataset(Dataset):
    def __init__(self, data):
        self.data = data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        x=self.data[idx][0]
        y=self.data[idx][1]
        return x, y
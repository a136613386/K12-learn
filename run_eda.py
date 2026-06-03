# run_eda.py
import os
import pandas as pd
from ydata_profiling import ProfileReport
from config import Config


def generate_eda_report():
    print("=== [第一步：正在读取并加载数据集] ===")
    if not os.path.exists(Config.RAW_JSON_DATA):
        raise FileNotFoundError(f"找不到数据集文件，请检查路径: {Config.RAW_JSON_DATA}")

    # 用 Pandas 指定并加载你的 500 多条生物题数据
    df = pd.read_json(Config.RAW_JSON_DATA)
    print(f"成功加载数据集：{os.path.basename(Config.RAW_JSON_DATA)}")
    print(f"当前样本总量: {len(df)} 条。")

    # 💡 核心优化：为了让 ydata-profiling 能够精准统计多标签的均衡性
    # 我们把 labels 列表中的每一个标签拆解出来，单独作为一个统计维度
    df_analysis = df.copy()
    df_analysis['labels_str'] = df_analysis['labels'].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)

    print("\n=== [第二步：启动 ydata-profiling 自动化审计引擎] ===")
    # explorative=True 会开启深度的文本字数、词频以及标签交叉关联分析
    profile = ProfileReport(
        df_analysis,
        title="K12 生物多标签分类数据集自动化 EDA 报告",
        explorative=True
    )

    # 将输出的 HTML 报告保存在你的 data 文件夹下，保持项目整洁
    output_html = os.path.join(Config.BASE_DIR, "data", "bio_dataset_report.html")

    print("\n=== [第三步：正在渲染并生成交互式 HTML 报告，请稍候...] ===")
    profile.to_file(output_html)
    print(f"\n🎉 恭喜！EDA 报告生成成功！")
    print(f"👉 报告已存盘，请直接去双击打开查看: {output_html}")


if __name__ == "__main__":
    generate_eda_report()
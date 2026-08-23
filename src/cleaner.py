# 数据清洗
import pandas as pd


def clean_data(df: pd.DataFrame):
    """
        清洗数据：去重、删除全空行、填充空值

        1. 删除完全空白的行
        2. 根据业务字段去重（排除"来源文件"列）
        3. 字符串列空值填充为"未知"，数字列填充为0

        :param df: 原始DataFrame
        :return: 清洗后的DataFrame
        """
    df_copy = df.copy()
    # 删除完全空白的行
    df_copy = df_copy.dropna(how="all")
    if "来源文件" in df_copy.columns:
        dedup_cols = [col for col in df_copy.columns if col != "来源文件"]
        # 删除重复行
        df_copy = df_copy.drop_duplicates(subset=dedup_cols)
    else:
        df_copy = df_copy.drop_duplicates()

    for col in df_copy.columns:
        if df_copy[col].dtype == "object":
            df_copy[col] = df_copy[col].fillna("未知")
        elif pd.api.types.is_numeric_dtype(df_copy[col]):
            df_copy[col] = df_copy[col].fillna(0)

    return df_copy

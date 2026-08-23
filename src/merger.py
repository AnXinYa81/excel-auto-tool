# 批量合成excel文档
import os
import pandas as pd


def merge_excel_files(folder_path: str):
    """
        读取文件夹下所有xlsx文件，合并成一张总表
        :param folder_path: excel存放文件夹路径
        :return: 合并后的DataFrame
    """
    df_list = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".xlsx") and not filename.startswith("~$"):
            file_path = os.path.join(folder_path, filename)#生成Excel对应根路径
            df = pd.read_excel(file_path)#pandas读取Excel文档
            df["来源文件"] = filename
            df_list.append(df)
    if not df_list:
        raise FileNotFoundError("文件夹内没有找到xlsx文件")

    total_df = pd.concat(df_list,ignore_index=True)
    return total_df


if __name__ == "__main__":
    data = merge_excel_files("../data/input")
    print(f"合并完成，一共{len(data)}条数据")



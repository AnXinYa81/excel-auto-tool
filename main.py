import os
from src.merger import merge_excel_files
from src.cleaner import clean_data

def main():
    input_dir ="./data/input"
    output_file="./data/output/汇总数据.xlsx"

    #1.批量合并
    raw_df = merge_excel_files(input_dir)
    print(f"原始数据行数：{len(raw_df)}")

    #2.数据清洗
    clean_df = clean_data(raw_df)
    print(f"清洗后的行数：{len(clean_df)}")

    #3.导出
    os.makedirs("./data/output", exist_ok=True)
    clean_df.to_excel(output_file,index=False)
    print(f"文件已输出至：{output_file}")

if __name__ == "__main__":
    main()
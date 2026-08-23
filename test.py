# test.py
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta


def generate_test_files():
    """生成完整字段测试Excel，覆盖analyzer全部接口（支持环比、同比、相关性计算）"""
    np.random.seed(42)

    # 基础维度
    name_list = ["张三", "李四", "王五", "赵六", "孙七"]
    dept_list = ["销售部", "市场部"]
    city_list = ["北京", "上海", "广州", "深圳", "杭州"]
    category_list = ["办公用品", "电子设备", "劳保用品"]
    product_list = {
        "办公用品": ["A4打印纸", "中性笔", "文件夹"],
        "电子设备": ["键盘", "鼠标", "显示器"],
        "劳保用品": ["手套", "安全帽"]
    }

    start_date = datetime(2025, 1, 1)
    month_files = {}

    # 生成1‑5月共5个excel文件
    for month_idx in range(5):
        current_month = start_date + timedelta(days=month_idx * 31)
        rows = []
        for _ in range(25):
            cat = np.random.choice(category_list)
            prod = np.random.choice(product_list[cat])
            sale_date = current_month + timedelta(days=np.random.randint(0, 28))
            sales = round(np.random.uniform(8000, 35000), 2)
            profit = round(sales * np.random.uniform(0.12, 0.35), 2)
            qty = np.random.randint(10, 120)

            row = {
                "姓名": np.random.choice(name_list),
                "部门": np.random.choice(dept_list),
                "城市": np.random.choice(city_list),
                "产品类别": cat,
                "产品名称": prod,
                "销售日期": sale_date.strftime("%Y-%m-%d"),
                "销售额": sales,
                "利润": profit,
                "销量": qty
            }
            rows.append(row)

        df_month = pd.DataFrame(rows)
        # 人为制造少量空值、重复行，用于测试清洗逻辑
        df_month.loc[np.random.choice(df_month.index, size=2), "利润"] = np.nan
        df_month = pd.concat([df_month, df_month.iloc[[0]]], ignore_index=True)

        file_name = f"销售数据{current_month.month}月.xlsx"
        month_files[current_month.month] = (df_month, file_name)

    os.makedirs("./data/input", exist_ok=True)
    for m, (df, fn) in month_files.items():
        full_path = os.path.join("./data/input", fn)
        df.to_excel(full_path, index=False)
        print(f"✅生成 {full_path}，{len(df)}行")

    print("\n🎉全部测试Excel生成完毕！字段齐全，支持全部分析函数")
    print("执行顺序：")
    print("1. python test.py      # 生成测试数据源")
    print("2. python main.py     # 合并+清洗，产出汇总数据.xlsx")
    print("3. python run_all.py  # 执行全部analyzer、visualizer，输出完整分析报告.xlsx")


if __name__ == "__main__":
    generate_test_files()

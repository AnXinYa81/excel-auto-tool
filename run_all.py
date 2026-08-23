# run_all.py
import pandas as pd
import os
from src.analyzer import (
    descriptive_stats,
    group_aggregate,
    pivot_table,
    top_n,
    add_mom_column,
    add_yoy_column,
    correlation_analysis,
    distribution_analysis,
    contribution_analysis
)
from src.visualizer import (
    bar_chart,
    pie_chart,
    line_chart,
    stacked_bar_chart,
    combo_chart,
    insert_image_to_excel
)


def main():
    df = pd.read_excel("./data/output/汇总数据.xlsx")
    print(f"读取汇总数据成功，总行数：{len(df)}")

    img_output = "./data/output/charts"
    os.makedirs(img_output, exist_ok=True)

    # 1.描述性统计
    stat_res = descriptive_stats(df, numeric_cols=["销售额", "利润", "销量"])
    print("\n【1.描述性统计】")
    print(stat_res)

    # 2.分组聚合：单聚合，避免列名带_sum后缀
    agg_res = group_aggregate(
        df,
        group_cols=["产品类别"],
        agg_dict={"销售额": "sum", "利润": "sum", "销量": "count"}
    )
    print("\n【2.分组聚合列名】", agg_res.columns.tolist())
    print(agg_res)

    # 3.透视表：行=城市，列=产品类别，值=销售额
    pivot_res = pivot_table(df, index="城市", columns="产品类别", values="销售额", aggfunc="sum")
    print("\n【3.透视表】")
    print(pivot_res)

    # 4.TopN：产品销售额Top8
    top_res = top_n(df, group_col="产品名称", value_col="销售额", n=8)
    print("\n【4.TopN产品】")
    print(top_res)

    # 5.环比增长率
    mom_res = add_mom_column(df, date_col="销售日期", value_col="销售额")
    print("\n【5.月度环比】")
    print(mom_res)

    # 6.同比增长率（测试数据只有5个月，大量NaN属于正常）
    yoy_res = add_yoy_column(df, date_col="销售日期", value_col="销售额")
    print("\n【6.月度同比】")
    print(yoy_res)

    # 7.相关性分析
    corr_res = correlation_analysis(df, numeric_cols=["销售额", "利润", "销量"])
    print("\n【7.相关性矩阵】")
    print(corr_res)

    # 8.分布分析：销售额分箱
    dist_res = distribution_analysis(df, value_col="销售额", bins=5)
    print("\n【8.销售额分布分箱】")
    print(dist_res)

    # 9.贡献度分析（帕累托）
    contrib_res = contribution_analysis(df, group_col="产品名称", value_col="销售额")
    print("\n【9.贡献度帕累托分析】")
    print(contrib_res)

    # ============ 绘图部分 ============
    bar1 = bar_chart(
        agg_res,
        x_col="产品类别",
        y_col="销售额",
        title="各类别总销售额",
        output_path=os.path.join(img_output, "cat_bar.png")
    )

    pie1 = pie_chart(
        top_res,
        label_col="产品名称",
        value_col="销售额",
        title="TOP8产品销售额占比",
        output_path=os.path.join(img_output, "top_pie.png")
    )

    line1 = line_chart(
        mom_res,
        x_col="月份",
        y_col="销售额",
        title="月度销售额趋势",
        output_path=os.path.join(img_output, "month_line.png")
    )

    # 堆叠柱状图数据源
    stack_df = group_aggregate(
        df,
        group_cols=["销售日期", "产品类别"],
        agg_dict={"销售额": "sum"}
    )
    stack_df["销售日期"] = pd.to_datetime(stack_df["销售日期"]).dt.strftime("%Y-%m")

    stack1 = stacked_bar_chart(
        stack_df,
        x_col="销售日期",
        y_col="销售额",
        stack_col="产品类别",
        title="每月各类别销售额堆叠",
        output_path=os.path.join(img_output, "stack_bar.png")
    )

    # 组合图：销售额柱状 + 环比增长率折线
    combo1 = combo_chart(
        mom_res,
        x_col="月份",
        bar_col="销售额",
        line_col="环比增长率(%)",
        title="月度销售额&环比增长率",
        output_path=os.path.join(img_output, "combo.png")
    )

    # 写入Excel报告，每个分析结果单独sheet
    report_path = "./data/output/完整分析报告.xlsx"
    with pd.ExcelWriter(report_path) as writer:
        stat_res.to_excel(writer, sheet_name="描述统计")
        agg_res.to_excel(writer, sheet_name="类别聚合", index=False)
        pivot_res.to_excel(writer, sheet_name="透视表")
        top_res.to_excel(writer, sheet_name="TOP产品", index=False)
        mom_res.to_excel(writer, sheet_name="环比", index=False)
        yoy_res.to_excel(writer, sheet_name="同比", index=False)
        corr_res.to_excel(writer, sheet_name="相关系数")
        dist_res.to_excel(writer, sheet_name="分布分箱", index=False)
        contrib_res.to_excel(writer, sheet_name="帕累托贡献度", index=False)

    # 把图片嵌入对应sheet，统一放在H列，避免覆盖表格数据
    insert_image_to_excel(report_path, bar1, sheet_name="类别聚合", cell="H2")
    insert_image_to_excel(report_path, pie1, sheet_name="TOP产品", cell="H2")
    insert_image_to_excel(report_path, line1, sheet_name="环比", cell="H2")
    insert_image_to_excel(report_path, stack1, sheet_name="透视表", cell="H20")
    insert_image_to_excel(report_path, combo1, sheet_name="环比", cell="H20")

    print(f"\n✅✅✅全部功能执行完毕，报告输出：{report_path}")


if __name__ == "__main__":
    main()

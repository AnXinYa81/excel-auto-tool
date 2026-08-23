"""
数据分析模块
功能：描述性统计、分组聚合、透视表、TopN 排名、环比/同比增长率、相关性分析、分布分析、贡献度分析

设计原则：
  - 每个函数接收 pandas DataFrame，返回 DataFrame，便于串联到报告模块
  - 函数参数尽量宽松，列名不存在时给出友好提示而非直接崩溃
  - 所有打印信息以 [分析] 开头，方便日志定位
"""
import pandas as pd
import numpy as np


# 1-----------描述性统计
def descriptive_stats(df: pd.DataFrame, numeric_cols: list = None) -> pd.DataFrame:
    """
       对数值列做描述性统计。

       在 pandas describe() 基础上额外补充：
         - 缺失数 / 缺失率：让清洗效果可量化
         - 偏度 (skew)：衡量分布对称性，>0 右偏、<0 左偏
         - 峰度 (kurt)：衡量尾部厚度，>0 比正态更尖、<0 更平
         - 变异系数 (CV)：标准差/均值，用于跨列比较离散程度

       :param df: 输入 DataFrame
       :param numeric_cols: 指定要统计的数值列；None 时自动选取所有数值列
       :return: 统计结果 DataFrame，索引为列名
       """
    if numeric_cols is None:
        cols = df.select_dtypes(include=[np.number]).columns.tolist()
    else:
        cols = [c for c in numeric_cols if c in df.columns]

    if not cols:
        print("[分析] 未找到数值列，返回空统计结果")
        return pd.DataFrame()

    stats = df[cols].describe().T  # T转置，列变行
    stats["缺失数"] = df[cols].isnull().sum()  # 空值个数
    stats["缺失率"] = (df[cols].isnull().mean() * 100).round(2).astype(str) + "%"

    stats["偏度"] = df[cols].skew(skipna=True).round(4)
    stats["峰度"] = df[cols].kurt(skipna=True).round(4)

    # 变异系数=标准差/均值（均值为0时设为NAN，避免除0
    cv = []
    for col in cols:
        mean_val = df[col].mean()
        cv.append(round(df[col].std() / mean_val, 4) if mean_val != 0 else np.nan)
    stats["变异系数"] = cv
    stats["count"] = stats["count"].astype(int)

    print(f"[分析]描述性统计完成，覆盖{len(cols)}个数值列")
    return stats


# 2------------分组聚合
def group_aggregate(
        df: pd.DataFrame,
        group_cols: list,
        agg_dict: dict
) -> pd.DataFrame:
    """
       按指定列分组并聚合。

       :param group_cols: 分组列列表，如 ["销售部门", "产品名称"]
       :param agg_dict: 聚合字典，键为列名、值为聚合函数名或函数列表
                        例如 {"销售金额": "sum", "订单号": "count"}
                        多聚合函数：{"销售金额": ["sum", "mean", "max"]}
       :return: 聚合结果 DataFrame（分组列已 reset_index 变为普通列）
       """
    # 校验列名存在
    valid_groups = [c for c in group_cols if c in df.columns]
    valid_aggs = {k: v for k, v in agg_dict.items() if k in df.columns}
    if not valid_groups or not valid_aggs:
        print("[分析] 分组聚合：指定的列不存在，返回空结果")
        return pd.DataFrame()

    result = df.groupby(valid_groups, dropna=False).agg(valid_aggs).reset_index()  # 分组，聚合，列名统一
    # 这边考虑agg_dict为列表
    if isinstance(result.columns, pd.MultiIndex):
        result.columns = [
            f"{a}_{b}" if b else a for a, b in result.columns
        ]

    print(f"[分析] 分组聚合完成，共 {len(result)} 组（分组列: {valid_groups}）")
    return result

    # 3------透视表


def pivot_table(
        df: pd.DataFrame,
        index: str,
        columns: str,
        values: str,
        aggfunc: str = "sum",
        fill_value=0
) -> pd.DataFrame:
    """
        生成二维透视表，自动添加行/列合计。

        :param index: 行维度列名
        :param columns: 列维度列名
        :param values: 数值列名
        :param aggfunc: 聚合函数，默认 sum
        :param fill_value: 空值填充值，默认 0
        :return: 透视表 DataFrame（含合计行/列）
        """
    if index not in df.columns or columns not in df.columns or values not in df.columns:
        print("[分析] 透视表：指定的列不存在，返回空结果")
        return pd.DataFrame()
    pivot = pd.pivot_table(
        df,
        index=index,
        columns=columns,
        values=values,
        aggfunc=aggfunc,
        fill_value=fill_value,
        margins=True,
        margins_name="合计",
    )
    print(f"[分析] 透视表生成完成（行: {index}, 列: {columns}, 值: {values}, 聚合: {aggfunc}）")
    return pivot


# 4-------TopN排名
def top_n(
        df: pd.DataFrame,
        group_col: str,
        value_col: str,
        n: int = 10,
        ascending: bool = False
) -> pd.DataFrame:
    """
        按分组列汇总数值列后取 TopN。

        :param group_col: 分组列（如 "产品名称"）
        :param value_col: 数值列（如 "销售金额"）
        :param n: 取前 N 名
        :param ascending: False=降序（金额最大的N个），True=升序（最小的N个）
        :return: 含排名、占比列的 DataFrame
        """
    if group_col not in df.columns or value_col not in df.columns:
        print("[分析] TopN：指定的列不存在，返回空结果")
        return pd.DataFrame()

    # 按分组列求和并排序
    result = (
        df.groupby(group_col, dropna=False)
        [value_col].sum().sort_values(ascending=ascending).head(n).reset_index()
    )
    result["排名"] = range(1, len(result) + 1)
    total = result[value_col].sum()
    if total != 0:
        result["占比"] = (result[value_col] / total * 100).round(2).astype(str) + "%"
    else:
        result["占比"] = "0%"
    print(f"[分析] Top{n} 排名完成（按 {value_col}，{'降序' if not ascending else '升序'}）")
    return result


# 5------------环比增长率
def add_mom_column(
        df: pd.DataFrame,
        date_col: str,
        value_col: str,
        group_col: str = None
) -> pd.DataFrame:
    """
        计算按月环比增长率。

        环比 = (本月值 - 上月值) / 上月值 × 100%
        第一个月没有上月数据，环比为 NaN。

        :param date_col: 日期列名（会自动转 datetime）
        :param value_col: 要计算环比的数值列
        :param group_col: 分组列（如 "产品名称"），None 表示整体计算
        :return: 含 "_月份" 和 "环比增长率" 列的 DataFrame
        """
    if date_col not in df.columns or value_col not in df.columns:
        print("[分析] 环比计算：指定的列不存在，返回空结果")
        return pd.DataFrame()

    df = df.copy()
    df["月份"] = pd.to_datetime(df[date_col], errors="coerce").dt.to_period("M")

    if group_col and group_col in df.columns:
        monthly = df.groupby([group_col, "月份"])[value_col].sum().reset_index()
        monthly["环比增长率(%)"] = monthly.groupby(group_col)[value_col].pct_change() * 100
    else:
        monthly = df.groupby("月份")[value_col].sum().reset_index()
        monthly["环比增长率(%)"] = monthly[value_col].pct_change() * 100

    monthly["环比增长率(%)"] = monthly["环比增长率(%)"].round(2)
    print(f"[分析] 环比增长率计算完成（按 {value_col}，分组: {group_col or '整体'}）")
    return monthly


# --------同比增长率
def add_yoy_column(
        df: pd.DataFrame,
        date_col: str,
        value_col: str,
        group_col: str = None
) -> pd.DataFrame:
    """
    计算按月同比增长率（与去年同月比较）。

    同比 = (本月值 - 去年同月值) / 去年同月值 × 100%
    需要至少两年的数据才有意义；数据不足时同比列为 NaN。

    :param date_col: 日期列名
    :param value_col: 数值列
    :param group_col: 分组列，None 表示整体
    :return: 含 "年", "月", "同比增长率(%)" 的 DataFrame
    """
    if date_col not in df.columns or value_col not in df.columns:
        print("[分析] 同比计算：指定的列不存在，返回空结果")
        return pd.DataFrame()

    df = df.copy()
    dt = pd.to_datetime(df[date_col], errors="coerce")
    df["_年"] = dt.dt.year
    df["_月"] = dt.dt.month

    if group_col and group_col in df.columns:
        monthly = df.groupby([group_col, "_年", "_月"])[value_col].sum().reset_index()
        # 按组内月份排序后，shift(12) 即去年同月
        monthly = monthly.sort_values([group_col, "_年", "_月"])
        monthly["同比增长率(%)"] = monthly.groupby(group_col)[value_col].pct_change(periods=12) * 100
    else:
        monthly = df.groupby(["_年", "_月"])[value_col].sum().reset_index()
        monthly = monthly.sort_values(["_年", "_月"])
        monthly["同比增长率(%)"] = monthly[value_col].pct_change(periods=12) * 100

    monthly["同比增长率(%)"] = monthly["同比增长率(%)"].round(2)

    print(f"[分析] 同比增长率计算完成（按 {value_col}，分组: {group_col or '整体'}）")
    return monthly


# 7-----------相关性分析
def correlation_analysis(
        df: pd.DataFrame, numeric_cols: list = None
) -> pd.DataFrame:
    """
    计算数值列之间的 Pearson 相关系数矩阵。

    相关系数范围 [-1, 1]：
      - 接近 1：强正相关
      - 接近 -1：强负相关
      - 接近 0：无线性相关

    :param df: 输入 DataFrame
    :param numeric_cols: 指定列；None 时自动选取所有数值列
    :return: 相关系数矩阵 DataFrame
    """
    if numeric_cols is None:
        cols = df.select_dtypes(include=[np.number]).columns.tolist()
    else:
        cols = [c for c in numeric_cols if c in df.columns]

    if len(cols) < 2:
        print("[分析] 相关性分析：至少需要2个数值列")
        return pd.DataFrame()

    corr = df[cols].corr(method="pearson").round(4)
    print(f"[分析] 相关性分析完成，共 {len(cols)} 个数值列")
    return corr


# ---------8分布分析（数值分箱）
def distribution_analysis(
        df: pd.DataFrame,
        value_col: str,
        bins: int = 5,
        labels: list = None,
) -> pd.DataFrame:
    """
        对数值列做等宽分箱，统计每个区间的频数和占比。

        :param value_col: 要分析的数值列
        :param bins: 分箱数量，默认5
        :param labels: 自定义区间标签，None 时自动生成
        :return: 含区间、频数、占比的 DataFrame
        """
    if value_col not in df.columns:
        print("[分析] 分布分析：指定的列不存在")
        return pd.DataFrame()
    series = df[value_col].dropna()
    # 等宽分箱
    binned = pd.cut(series, bins=bins, labels=labels, include_lowest=True)  # 组1：1-100，组2：100-200.....
    dist = binned.value_counts().sort_index().reset_index()  # 确定区间数量
    dist.columns = ["区间", "频数"]

    total = dist["频数"].sum()
    dist["占比"] = (dist["频数"] / total * 100).round(2).astype(str) + "%"
    print(f"[分析] 分布分析完成（列: {value_col}，分箱数: {bins}）")
    return dist


# 9-----------贡献度分析
def contribution_analysis(
        df: pd.DataFrame,
        group_col: str,
        value_col: str,
) -> pd.DataFrame:
    """
       计算每个分组对总体的贡献度（占比 + 累计占比）。

       累计占比可用于帕累托分析（80/20法则）：
       找到累计占比达到 80% 的那些组，即为核心贡献来源。

       :param group_col: 分组列
       :param value_col: 数值列
       :return: 按金额降序排列，含占比和累计占比的 DataFrame
       """
    if group_col not in df.columns or value_col not in df.columns:
        print("[分析] 贡献度分析：指定的列不存在")
        return pd.DataFrame()

    result = df.groupby(group_col, dropna=False)[value_col].sum().sort_values(ascending=False).reset_index()
    total = result[value_col].sum()
    if total == 0:
        result["贡献度"] = "0%"
        result["累计贡献度"] = "0%"
        return result
    result["贡献度"] = (result[value_col] / total * 100).round(2)
    result["累计贡献度"] = result["贡献度"].cumsum().round(2)
    result["是否核心（80%）"] = result["累计贡献度"].apply(
        lambda x: "是" if x <= 80 else "否"
    )
    result["贡献度"] = result["贡献度"].astype(str) + "%"
    result["累计贡献度"] = result["累计贡献度"].astype(str) + "%"

    print(f"[分析] 贡献度分析完成（分组: {group_col}，数值: {value_col}）")
    return result

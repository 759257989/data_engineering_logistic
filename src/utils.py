"""共享工具:统一的路径定义 + 列名规范化函数。"""
from pathlib import Path
import re

# 项目根目录 = 本文件(src/utils.py)往上两级
# parents[0] 是 src/,parents[1] 是项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = PROJECT_ROOT / "data" / "source"   # 原始文件
RAW_DIR = PROJECT_ROOT / "data" / "raw"          # raw 层输出


def to_snake_case(name: str) -> str:
    """把任意列名转成 snake_case(全小写 + 下划线分隔)。

    例:'Days for shipping (real)' -> 'days_for_shipping_real'
        'PULocationID'            -> 'pu_location_id'

    这是一种机械、无损的规范化:只改名字格式,不改数据本身,
    所以放在 raw 层是允许的。目的是让后续 SQL 不必给列名处处加引号。
    """
    name = str(name).strip()
    name = re.sub(r'(?<=[a-z0-9])(?=[A-Z])', '_', name)    # 驼峰边界:aB -> a_B
    name = re.sub(r'(?<=[A-Z])(?=[A-Z][a-z])', '_', name)  # 缩写边界:ABCd -> AB_Cd
    name = re.sub(r'[^0-9a-zA-Z]+', '_', name)             # 空格/括号/符号 -> _
    name = re.sub(r'_+', '_', name)                        # 多个 _ 合并成一个
    return name.strip('_').lower()                         # 去掉首尾 _ 并转小写
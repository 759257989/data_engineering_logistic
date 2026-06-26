"""
Phase 1 · 把本地 raw parquet 上传到 S3
--------------------------------------
把 data/raw/ 下的所有 parquet,原样上传到 s3://<桶>/raw/ 下,
保持和本地一样的目录结构(dataco/、nyc_tlc/、reference/ ...)。

运行:  python src/ingestion/upload_to_s3.py
"""
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import boto3
from dotenv import load_dotenv
from utils import RAW_DIR


def upload_raw(s3_client, raw_dir: Path, bucket: str, prefix: str = "raw") -> list[str]:
    """把 raw_dir 下所有 parquet 上传到 s3://bucket/prefix/...,返回上传后的 key 列表。

    这个函数特意把 s3_client 作为参数传入(而不是在函数里直接创建),
    好处是测试时可以传入一个"假的"S3 客户端来验证逻辑,不必真的连 AWS。
    """
    keys = []
    for path in sorted(raw_dir.rglob("*.parquet")):       # 递归找出所有 parquet
        rel = path.relative_to(raw_dir)                   # 相对路径,如 dataco/supply_chain.parquet
        key = f"{prefix}/{rel.as_posix()}"                # 拼成 S3 的 key:raw/dataco/supply_chain.parquet
        s3_client.upload_file(str(path), bucket, key)     # 真正上传这一个文件
        size_mb = path.stat().st_size / 1024 / 1024
        print(f"  上传 {key}  ({size_mb:.1f} MB)")
        keys.append(key)
    return keys


def main() -> None:
    load_dotenv()                                         # 把 .env 里的变量读进环境变量
    bucket = os.environ["S3_BUCKET"]
    # 显式地把密钥传给 boto3,让"凭证从哪来"一目了然
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        region_name=os.environ.get("AWS_REGION", "us-east-1"),
    )
    print(f"开始上传到 s3://{bucket}/raw/ ...")
    keys = upload_raw(s3, RAW_DIR, bucket)
    print(f"\n完成,共上传 {len(keys)} 个文件。")


if __name__ == "__main__":
    main()
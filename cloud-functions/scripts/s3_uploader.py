import os
import sys
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, NoCredentialsError

# 尝试加载 .env 文件（如果存在）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# S3 兼容对象存储配置（从环境变量读取）
S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL", "https://s3.bitiful.net")
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "development")
S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY", "")
S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY", "")

# 上传配置（从环境变量读取，提供默认值）
_local_data_dir = os.environ.get("LOCAL_DATA_DIR")
_script_dir = Path(__file__).parent
if _local_data_dir:
    _local_path = Path(_local_data_dir)
    # 如果是相对路径，基于脚本目录解析
    if not _local_path.is_absolute():
        LOCAL_DATA_DIR = _script_dir / _local_path
    else:
        LOCAL_DATA_DIR = _local_path
else:
    LOCAL_DATA_DIR = _script_dir / 'output' / 'derived'

S3_UPLOAD_PREFIX = os.environ.get("S3_UPLOAD_PREFIX", "DiviQuant/")


def create_s3_client():
    if not S3_ACCESS_KEY or not S3_SECRET_KEY:
        print("错误: 未检测到 S3_ACCESS_KEY/S3_SECRET_KEY。")
        print("")
        print("方式一：使用 .env 文件（推荐）")
        print("  1. cp .env.example .env")
        print("  2. 编辑 .env 文件填入密钥")
        print("  3. pip install python-dotenv")
        print("")
        print("方式二：直接设置环境变量")
        print("  export S3_ACCESS_KEY=your_key")
        print("  export S3_SECRET_KEY=your_secret")
        print("")
        print("可选环境变量：")
        print("  S3_ENDPOINT_URL=https://s3.bitiful.net")
        print("  S3_BUCKET_NAME=development")
        print("  S3_UPLOAD_PREFIX=DiviQuant/")
        sys.exit(1)

    config = Config(
        signature_version="s3v4",
        s3={"addressing_style": "path"},
        retries={"max_attempts": 3, "mode": "standard"},
    )

    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT_URL,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        config=config,
    )


def test_connectivity(s3_client):
    try:
        print(f"正在验证存储桶 {S3_BUCKET_NAME} 的连通性...")
        s3_client.head_bucket(Bucket=S3_BUCKET_NAME)
        print("✅ 连通性验证成功。")
    except NoCredentialsError:
        print("错误: 找不到凭证，请检查环境变量。")
        sys.exit(1)
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code")
        print(f"❌ 连通性验证失败: {code}")
        print(exc)
        sys.exit(1)


def list_objects(s3_client, prefix="", max_items=100):
    print(f"正在列出存储桶 {S3_BUCKET_NAME} 下的对象，前缀: '{prefix}'...")
    paginator = s3_client.get_paginator("list_objects_v2")
    page_iterator = paginator.paginate(
        Bucket=S3_BUCKET_NAME, Prefix=prefix, PaginationConfig={"PageSize": max_items})

    found = False
    for page in page_iterator:
        contents = page.get("Contents", [])
        if not contents:
            continue
        found = True
        for obj in contents:
            key = obj.get("Key")
            size = obj.get("Size")
            last_modified = obj.get("LastModified")
            print(f"- {key}  ({size} bytes, {last_modified})")

    if not found:
        print("(存储桶中未找到任何对象，或前缀下无对象。)")


def get_remote_object_keys(s3_client, prefix: str) -> set[str]:
    """批量获取 S3 指定前缀下的所有对象 key，返回 set 用于快速查找。"""
    keys = set()
    paginator = s3_client.get_paginator("list_objects_v2")
    page_iterator = paginator.paginate(
        Bucket=S3_BUCKET_NAME, Prefix=prefix, PaginationConfig={"PageSize": 1000})

    for page in page_iterator:
        for obj in page.get("Contents", []):
            keys.add(obj["Key"])

    return keys


def upload_file(s3_client, local_path: Path, remote_key: str, existing_keys: set[str]) -> None:
    """上传单个文件到 S3，根据本地缓存的存在性判断是新增还是更新。"""
    exists = remote_key in existing_keys
    action = "更新" if exists else "新增"

    print(f"  [{action}] {local_path.name} -> s3://{S3_BUCKET_NAME}/{remote_key}")
    s3_client.upload_file(str(local_path), S3_BUCKET_NAME, remote_key)


def upload_directory(s3_client, data_dir: str, remote_dir: str) -> None:
    """将本地目录下的所有文件上传到 S3 的指定远程目录。"""
    local_path = Path(data_dir).resolve()

    if not local_path.exists():
        print(f"错误: 本地目录不存在: {local_path}")
        return

    if not local_path.is_dir():
        print(f"错误: 指定路径不是目录: {local_path}")
        return

    # 确保 remote_dir 以 / 结尾，且不以 / 开头
    remote_prefix = remote_dir.strip('/')
    if remote_prefix:
        remote_prefix += '/'

    print(f"\n开始上传目录: {local_path}")
    print(f"远程目标: s3://{S3_BUCKET_NAME}/{remote_prefix}")

    files = [f for f in local_path.iterdir() if f.is_file()]
    if not files:
        print("(本地目录中没有文件)")
        return

    # 批量获取远程文件列表（1 次 API 调用）
    print(f"正在获取远程文件列表...")
    existing_keys = get_remote_object_keys(s3_client, remote_prefix)
    print(f"发现 {len(existing_keys)} 个远程文件")

    # 上传文件，使用本地缓存判断存在性
    for file_path in files:
        remote_key = f"{remote_prefix}{file_path.name}"
        upload_file(s3_client, file_path, remote_key, existing_keys)

    print(f"\n上传完成，共处理 {len(files)} 个文件。")


if __name__ == "__main__":
    s3_client = create_s3_client()
    test_connectivity(s3_client)
    upload_directory(s3_client, LOCAL_DATA_DIR, S3_UPLOAD_PREFIX)

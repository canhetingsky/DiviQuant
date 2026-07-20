# GitHub Actions 配置说明

## 数据更新工作流

[数据更新工作流](file:///f:/Desktop/AI-Code/DiviQuant/.github/workflows/data-update.yml) 会自动生成股息数据并上传到 S3 对象存储。

### 触发方式

1. **定时触发**: 每个工作日 UTC 时间 07:00（北京时间 15:00，A股收盘后）自动执行
2. **手动触发**: 在 GitHub 仓库的 Actions 页面点击 "Run workflow"

### 执行流程

```
┌─────────────────────────────────────────────────────────────┐
│                   Job: generate-and-upload                  │
│  1. 检出代码                                                │
│  2. 设置 Python 环境 (3.11)                                │
│  3. 恢复缓存 (output/cache/)                                │
│  4. 安装依赖 (pip install -r requirements.txt)             │
│  5. 运行 dividend_data_generator.py 生成数据                │
│  6. 运行 s3_uploader.py 上传数据到 S3                       │
│  7. 保存缓存 (output/cache/)                                │
└─────────────────────────────────────────────────────────────┘
```

### GitHub Secrets 配置

在仓库设置 → Secrets and variables → Actions 中添加以下 secrets：

| Secret 名称        | 必填 | 默认值                   | 说明                   |
| ------------------ | ---- | ------------------------ | ---------------------- |
| `S3_ACCESS_KEY`    | ✅    | -                        | S3 访问密钥            |
| `S3_SECRET_KEY`    | ✅    | -                        | S3 秘密密钥            |
| `S3_ENDPOINT_URL`  | ❌    | `https://s3.bitiful.net` | S3 端点地址            |
| `S3_BUCKET_NAME`   | ❌    | `development`            | 存储桶名称             |
| `S3_UPLOAD_PREFIX` | ❌    | `DiviQuant/`             | 上传前缀               |
| `HTTP_PROXY`       | ❌    | -                        | HTTP 代理（如果需要）  |
| `HTTPS_PROXY`      | ❌    | -                        | HTTPS 代理（如果需要） |

**最小配置**：只需要 `S3_ACCESS_KEY` 和 `S3_SECRET_KEY`，其他使用默认值。

### 配置示例

```bash
# 必填配置（最小配置）
S3_ACCESS_KEY=ScKazMsU5qLaxQ9E1qRWeuLf
S3_SECRET_KEY=xbIQYDcP871h9wLHAEO8xy0Uqs25ozB

# 可选配置（如果需要自定义）
# S3_ENDPOINT_URL=https://s3.bitiful.net
# S3_BUCKET_NAME=development
# S3_UPLOAD_PREFIX=DiviQuant/

# 代理配置（可选）
# HTTP_PROXY=http://127.0.0.1:7890
```

### 手动触发

1. 打开 GitHub 仓库页面
2. 点击顶部导航栏的 "Actions"
3. 在左侧找到 "Update Dividend Data"
4. 点击 "Run workflow"
5. 选择分支，点击 "Run workflow"

### 查看日志

1. 打开 GitHub 仓库页面
2. 点击顶部导航栏的 "Actions"
3. 找到 "Update Dividend Data"
4. 点击最新的运行记录查看详细日志

### 注意事项

1. **时区**: `0 7 * * 1-5` 是 UTC 时间 07:00 = 北京时间 15:00（A股收盘后）
2. **缓存机制**: 使用 GitHub Actions Cache 持久化 `output/cache/` 目录，API 失败时可以使用缓存数据
3. **条件上传**: 只有数据生成成功才会执行 S3 上传，避免上传空数据
4. **运行时间**: 数据生成预计 10-30 分钟
5. **代理**: 如果 GitHub Actions 无法访问 AkShare 数据源，配置 `HTTP_PROXY`/`HTTPS_PROXY`
6. **前端**: 前端部署在其他地方，此工作流不包含前端构建和上传步骤

### 缓存保留策略

GitHub Actions Cache 有以下限制：

| 限制                  | 说明                                     |
| --------------------- | ---------------------------------------- |
| **7天未访问自动删除** | 缓存如果7天内没有被读取，会被自动清理    |
| **10GB/仓库**         | 所有缓存的总大小限制为10GB（免费账户）   |
| **LRU淘汰**           | 超过存储限制时，最久未使用的缓存会被删除 |
| **Key不可变**         | 缓存key一旦创建不能修改，只能生成新缓存  |

**当前工作流的缓存策略**：

- 使用 `dividend-cache-${{ github.run_date }}` 作为缓存key
- 每天生成一个新缓存（基于日期）
- 通过 `restore-keys: dividend-cache-` 回退到最近的缓存
- 由于工作日每天运行，缓存会被定期访问，不会触发7天未访问删除
- 周末（周六、周日）不运行，周五生成的缓存到下周一访问间隔3天，仍在7天内

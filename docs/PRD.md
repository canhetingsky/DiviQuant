# DiviQuant 多指数股息率看板 PRD 与技术实现方案

## 一、产品概述

产品名称建议：`DiviQuant 指数股息率看板`

产品定位：

- 一个基于本地或静态 JSON 数据的多指数股息率展示网站
- 首页先展示指数级概览
- 点击某个指数后，进入该指数的成分股详情页
- 支持电脑、平板、手机多端访问

核心价值：

- 从“单指数脚本输出”升级为“多指数可视化分析入口”
- 帮助用户快速比较不同指数的整体股息率特征
- 帮助用户下钻查看某个指数的高股息成分股明细

## 二、目标用户

1. 关注高股息策略的个人投资者
2. 做指数比较和成分股筛选的研究用户
3. 希望把 Python 分析结果转成网页可视化的使用者

## 三、产品目标

1. 支持多个指数的数据展示
2. 首页能快速比较不同指数的整体表现
3. 详情页能查看某个指数的成分股股息率列表
4. 全站响应式，适配手机、平板、桌面
5. 不依赖后端接口，优先使用静态 JSON 驱动

## 四、功能范围

### 4.1 首页：指数总览页

目标：

- 让用户先看到“有哪些指数”
- 让用户快速比较这些指数的整体特征

展示内容：

- 指数名称
- 指数代码
- 成分股数量
- 平均股息率
- 最高股息率
- 中位数股息率
- 数据更新时间
- 卡片点击进入详情页

交互：

- 支持按指数名称或代码搜索
- 支持按平均股息率排序
- 支持卡片视图
- 手机端采用单列卡片，桌面端采用多列卡片

### 4.2 指数详情页

目标：

- 展示单个指数的核心统计和成分股明细

展示内容：

- 指数名称、指数代码
- 数据更新时间
- 成分股总数
- 平均股息率
- 中位数股息率
- 最高股息率
- 最低股息率
- Top 10 高股息成分股图表
- 成分股表格

成分股表格字段：

- 排名
- 股票代码
- 股票名称
- 纳入日期
- 当前价格
- TTM 分红
- TTM 股息率

交互：

- 按代码或名称搜索
- 按股息率区间筛选
- 按表头排序
- 手机端表格可切为卡片列表
- 点击某条成分股可展开更多信息

### 4.3 可选增强功能

首版可以不做，但技术上预留：

- 指数间对比页
- 多日期快照切换
- 收藏指数
- 导出当前筛选结果
- 主题切换

## 五、信息架构

建议结构：

1. `/`
   首页，指数总览页
2. `/index/:indexCode`
   单个指数详情页

如果后续扩展：

3. `/compare`
   指数对比页

## 六、数据方案

建议不要直接把每个指数散落成独立文件后再靠前端“猜目录”，而是定义统一的数据组织方式。

### 6.1 推荐目录结构

```text
web/
  public/
    data/
      indexes.json
      index_000922_dividend_yield.json
      index_000015_dividend_yield.json
      index_399XXX_dividend_yield.json
```

### 6.2 首页索引文件 `indexes.json`

作用：

- 首页只需要读取一个总索引文件，就能知道有哪些指数
- 每个指数卡片所需的摘要信息都放这里
- 点击后再加载对应详情 JSON

建议字段：

```json
[
  {
    "index_code": "000922",
    "index_name": "中证红利",
    "file": "index_000922_dividend_yield.json",
    "stock_count": 100,
    "avg_yield": 5.21,
    "median_yield": 4.88,
    "max_yield": 11.26,
    "min_yield": 0.32,
    "updated_at": "2026-05-03 14:30:00"
  }
]
```

### 6.3 单指数详情文件

沿用当前明细结构，但建议补充元信息。推荐改成：

```json
{
  "index_info": {
    "index_code": "000922",
    "index_name": "中证红利",
    "updated_at": "2026-05-03 14:30:00",
    "stock_count": 100,
    "avg_yield": 5.21,
    "median_yield": 4.88,
    "max_yield": 11.26,
    "min_yield": 0.32
  },
  "stocks": [
    {
      "symbol": "601919",
      "stock_name": "中远海控",
      "included_date": "2024-12-16",
      "current_price": 14.12,
      "ttm_dividend": 1.59,
      "ttm_yield": 11.26
    }
  ]
}
```

这样前端会更顺手：

- 首页用 `indexes.json`
- 详情页用单指数 JSON
- 不需要前端再重复计算太多统计数据

## 七、页面与交互设计要求

### 7.1 首页

- 桌面端：3 到 4 列指数卡片
- 平板端：2 列
- 手机端：1 列
- 顶部可放全局说明、数据更新时间和搜索框

### 7.2 详情页

- 顶部展示指数摘要
- 中部展示图表
- 下方展示成分股列表
- 手机端表格区域可横向滚动，或切换为卡片式列表

### 7.3 响应式要求

- 手机：`<640px`
- 平板：`640px-1024px`
- 桌面：`>=1024px`

### 7.4 视觉风格

- 金融信息产品风格
- 强调数字可读性
- 高股息率用正向高亮色
- 不做花哨动效，优先稳定、清晰、专业

## 八、非功能需求

1. 性能
   首页首次加载应只请求 `indexes.json`
   详情页按需加载单个指数 JSON
   避免首页一次性加载所有明细文件

2. 可维护性
   组件拆分清晰
   数据结构统一
   前端逻辑与 Python 生成逻辑解耦

3. 兼容性
   支持主流现代浏览器
   支持桌面、平板、手机访问

4. 部署
   支持静态部署
   不依赖数据库和后端服务

## 九、技术实现方案

### 9.1 技术栈

前端：

- `Vue 3`
- `Vite`
- `Tailwind CSS`
- `Vue Router`
- `ECharts`
- `dayjs`

数据获取：

- 浏览器原生 `fetch`

原因：

- Vue 3 适合中小型数据看板
- Vite 构建快，静态部署方便
- Tailwind 做响应式很高效
- Vue Router 能自然支持“首页 -> 详情页”
- ECharts 适合金融数据图表

### 9.2 前端模块划分

建议组件：

- `IndexCard`
  首页单个指数卡片
- `IndexGrid`
  首页指数卡片列表
- `GlobalSearchBar`
  首页搜索和排序
- `IndexSummary`
  详情页顶部统计摘要
- `YieldChart`
  Top 10 股息率图表
- `StockTable`
  桌面端表格
- `StockCardList`
  手机端卡片列表
- `FilterPanel`
  详情页筛选器

### 9.3 路由方案

```text
/                   -> 首页，多指数总览
/index/000922       -> 中证红利详情
/index/000015       -> 上证红利详情
```

### 9.4 数据加载策略

首页：

- 加载 `indexes.json`
- 渲染指数卡片
- 不加载成分股详情

详情页：

- 根据路由参数 `indexCode`
- 查找对应详情文件
- 加载该指数 JSON
- 渲染统计、图表、表格

这样能保证：

- 首页速度快
- 数据量变大后仍可扩展
- 多指数支持清晰

## 十、与 Python 侧的衔接方案

当前 Python 脚本建议后续升级为两个输出层：

1. 输出单指数详情 JSON
   每个指数一个文件
2. 输出首页索引 `indexes.json`
   汇总所有指数的摘要信息

也就是 Python 负责：

- 数据抓取
- 数据清洗
- 统计聚合
- 生成前端可直接消费的 JSON

前端负责：

- 读取 JSON
- 展示和交互

这会是最稳的职责划分。

## 十一、首版开发范围建议

建议 MVP 做这些：

1. 首页指数卡片列表
2. 首页搜索和排序
3. 指数详情页
4. 详情页统计卡片
5. Top 10 股息率图表
6. 成分股表格或手机卡片列表
7. 响应式适配

先不做：

- 用户系统
- 后端 API
- 实时更新
- 多指数同屏深度对比
- 复杂权限或缓存系统

## 十二、开发阶段建议

### 阶段 1：数据规范

- 统一多指数 JSON 结构
- 生成 `indexes.json`

### 阶段 2：前端骨架

- 建立 Vue + Vite 项目
- 配置路由和基础布局
- 接入 Tailwind

### 阶段 3：首页

- 指数总览卡片
- 搜索和排序

### 阶段 4：详情页

- 指数摘要
- 图表
- 表格和筛选

### 阶段 5：响应式优化

- 手机、平板、桌面适配
- 表格与卡片列表切换

### 阶段 6：部署

- 打包为静态站点
- 本地或平台部署

## 十三、风险与注意点

1. 当前 JSON 结构如果只包含股票列表，首页摘要会不够方便
   建议新增 `indexes.json`

2. 如果未来指数数量多、每个指数股票多
   一定要按需加载，不能首页全量拉取

3. 如果纳入日期、价格、股息率存在空值
   前端要做空值展示策略，比如 `--`

4. 纯静态站点读取本地 JSON 时
   本地直接双击 HTML 可能遇到跨域或文件协议限制
   开发时建议走 Vite 本地服务

## 十四、Python 数据生成脚本架构

### 14.1 脚本位置

```
cloud-functions/scripts/
├── dividend_data_generator.py    # 主数据生成脚本
├── s3_uploader.py                # S3 上传工具
├── requirements.txt              # Python 依赖
├── .env.example                  # 环境变量模板
├── .gitignore                    # Git 忽略规则
└── output/                       # 输出目录
    ├── cache/                    # 缓存层（中间数据）
    │   ├── stock_universe.json
    │   ├── stock_dividend_cache.json
    │   ├── stock_price_cache.json
    │   ├── index_constituents/
    │   └── stock_dividend_raw/
    └── derived/                  # 派生层（前端使用）
        ├── indexes.json
        ├── all_stocks_dividend_yield.json
        ├── stock_dividend_summary.json
        ├── index_000015_dividend_yield.json
        ├── index_000300_dividend_yield.json
        ├── index_000922_dividend_yield.json
        ├── index_399324_dividend_yield.json
        ├── index_H30269_dividend_yield.json
        └── stock_dividend_history/
```

### 14.2 缓存策略

| 缓存文件 | TTL | 说明 |
|---------|-----|------|
| `stock_universe.json` | 24小时 | 全A股股票池 |
| `stock_dividend_cache.json` | 24小时 | TTM股息汇总缓存 |
| `stock_price_cache.json` | 24小时 | 最新股价缓存 |
| `index_constituents/*.json` | 7天 | 指数成分股列表 |
| `stock_dividend_raw/*.json` | 30天 | 单只股票完整分红历史 |

### 14.3 生成文件说明

#### 首页索引 `indexes.json`
- **用途**: 首页指数卡片展示
- **字段**: 指数代码、名称、成分股数量、平均/中位/最高股息率

#### 指数详情 `index_{code}_dividend_yield.json`
- **用途**: 单个指数详情页
- **字段**: 指数元信息、成分股列表（含TTM股息率）

#### 全市场股息率 `all_stocks_dividend_yield.json`
- **用途**: 全市场股票股息率排行榜
- **字段**: 股票代码、名称、当前价格、TTM分红、TTM股息率、排名

#### 分红汇总 `stock_dividend_summary.json`
- **用途**: 历史分红统计排行
- **字段**: 累计分红、年均分红、连续分红年限

#### 历史分红 `stock_dividend_history/{symbol}.json`
- **用途**: 单只股票历年分红详情
- **字段**: 年度分红汇总、分红次数、分红明细

### 14.4 支持的指数

| 指数代码 | 指数名称 |
|---------|---------|
| 000922 | 中证红利 |
| 000015 | 上证红利 |
| 399324 | 深证红利 |
| 000300 | 沪深300 |
| H30269 | 红利低波指数 |

### 14.5 S3 上传配置

脚本支持从环境变量读取配置：

```bash
# 必填
export S3_ACCESS_KEY=your_access_key
export S3_SECRET_KEY=your_secret_key

# 可选（有默认值）
export S3_ENDPOINT_URL=https://s3.bitiful.net
export S3_BUCKET_NAME=development
export S3_UPLOAD_PREFIX=DiviQuant/
```

或使用 `.env` 文件：
```bash
cp .env.example .env
# 编辑 .env 文件
pip install python-dotenv
python s3_uploader.py
```

### 14.6 运行流程

```bash
# 1. 安装依赖
cd cloud-functions/scripts
pip install -r requirements.txt

# 2. 生成数据
python dividend_data_generator.py

# 3. 配置 S3（可选）
cp .env.example .env
# 编辑 .env 填入密钥

# 4. 上传数据
python s3_uploader.py
```

---

## 十五、最终推荐结论

推荐产品形态：

- 多指数总览首页
- 单指数详情页
- **全市场股票股息率排行榜**
- **历史分红统计排行**
- 静态 JSON 驱动
- 全响应式数据看板

推荐技术栈：

- **前端**: `Vue 3 + Vite + Tailwind CSS + Vue Router + ECharts + dayjs`
- **数据**: `Python + AkShare + Pandas`
- **存储**: `S3 兼容对象存储`

推荐数据架构：

- 一个 `indexes.json` 做首页索引
- 多个 `index_xxx_dividend_yield.json` 做指数详情
- `all_stocks_dividend_yield.json` 全市场股息率
- `stock_dividend_summary.json` 分红统计汇总

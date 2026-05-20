# DiviQuant

一个基于 `AkShare` 的 A 股股息率数据准备脚本。

当前项目的重点是先把网页需要的结构化 JSON 数据准备好，而不是直接做前端页面。脚本会：

- 获取全 A 股股票池
- 缓存全 A 股最近 12 个月分红数据
- 缓存全 A 股最新价格数据
- 缓存指数成分股列表
- 生成指数详情 JSON 和首页索引 JSON

当前版本只输出 `JSON`，不再输出 `CSV`。

## 项目目标

这个脚本服务于一个多指数股息率展示页面，数据流分成三层：

1. 基础数据层
- 全 A 股股票池
- 全 A 股分红缓存
- 全 A 股价格缓存

2. 指数成分层
- 每个指数的成分股缓存

3. 派生结果层
- 指数详情 JSON
- 首页 `indexes.json`

网页只需要读取派生结果层。

## 目录结构

```text
output/
  cache/
    stock_universe.json
    stock_dividend_cache.json          # TTM股息汇总缓存
    stock_dividend_raw/                # 原始分红明细缓存
      000001.json
      000002.json
      ...
    stock_price_cache.json
    index_constituents/
      000015.json
      000300.json
      000922.json
      399324.json
  derived/
    indexes.json
    index_000015_dividend_yield.json
    index_000300_dividend_yield.json
    index_000922_dividend_yield.json
    index_399324_dividend_yield.json
    stock_dividend_summary.json        # 全市场分红统计汇总
    stock_dividend_history/            # 单只股票历史分红汇总
      000001.json
      000002.json
      ...
```

说明：

- `output/cache/` 用于缓存原始或半加工数据，避免重复请求
  - `stock_dividend_raw/` 保存每只股票的历史分红原始数据（30天缓存）
- `output/derived/` 用于保存前端直接读取的结果文件
  - `stock_dividend_history/` 保存每只股票的历史分红统计汇总
  - `stock_dividend_summary.json` 全市场分红统计汇总

## 数据处理流程

脚本入口在 [dividend_data_generator.py](F:\Desktop\AI-Code\DiviQuant\web\scripts\dividend_data_generator.py:1)。

完整流程如下：

1. 创建输出目录（包括新增的分红缓存目录）
2. 读取或刷新全 A 股股票池缓存
3. 读取或刷新每个指数的成分股缓存
4. 读取或刷新全 A 股分红缓存
   - 逐只获取原始分红数据并缓存到 `stock_dividend_raw/`
   - 计算 TTM 股息并缓存到 `stock_dividend_cache.json`
5. 读取或刷新全 A 股价格缓存
6. 合并分红缓存和价格缓存，形成全市场股票指标映射
7. **生成每只股票的历史分红汇总**（新增）
   - 基于原始分红数据生成年度统计
   - 保存到 `stock_dividend_history/`
8. **生成全市场分红统计汇总**（新增）
   - 汇总所有股票的分红统计
   - 保存到 `stock_dividend_summary.json`
9. 按指数成分股筛选并计算个股股息率
10. 生成每个指数的详情 JSON
11. 汇总生成首页使用的 `indexes.json`

当前流程的关键优化点：

- 分红是逐只股票抓取，但有日级缓存
- **原始分红数据缓存 30 天**，减少 API 调用
- 价格不是逐只历史行情抓取，而是一次性批量获取全市场最新价
- 指数成分股有独立缓存，不会每次都重新抓取

## 缓存策略

当前缓存有效期配置在 [dividend_data_generator.py](F:\Desktop\AI-Code\DiviQuant\web\scripts\dividend_data_generator.py:14) 附近：

- `STOCK_UNIVERSE_TTL_HOURS = 24`
- `DIVIDEND_CACHE_TTL_HOURS = 24`
- `DIVIDEND_RAW_TTL_HOURS = 24 * 30`（新增）
- `PRICE_CACHE_TTL_HOURS = 24`
- `INDEX_CONSTITUENTS_TTL_HOURS = 24 * 7`

含义：

- 全 A 股股票池：24 小时
- 全 A 股 TTM 分红缓存：24 小时
- **原始分红数据缓存：30 天**（历史分红数据相对稳定）
- 全 A 股价格缓存：24 小时
- 指数成分股缓存：7 天

缓存校验规则：

- 通过 `updated_at` 和 `expires_at` 判断是否过期
- 对价格缓存额外做了坏缓存保护
  - 如果缓存虽然没过期，但所有 `current_price` 都是空值
  - 脚本会自动认定它无效并重新生成
- **对无分红数据的股票做特殊处理**
  - 如果 API 返回无数据错误，缓存空记录（30天）
  - 避免重复请求确实没有分红的股票

## 代码标准化规则

脚本内部统一使用 6 位纯数字股票代码，例如：

- `000001`
- `600036`
- `920000`

注意不同接口返回的代码格式不一致：

- 股票池接口返回：`000001`
- 指数成分股接口返回：`000090`
- 新浪批量行情接口返回：`sz000065`、`sh600036`、`bj920000`

脚本中的 `normalize_symbol()` 会自动做标准化处理：

- 去掉 `sh`、`sz`、`bj` 等市场前缀
- 提取数字部分
- 保留最后 6 位代码

示例：

```text
sz000065 -> 000065
sh600036 -> 600036
bj920000 -> 920000
```

这个标准化过程是价格缓存能正确对齐股票池的关键。

## 输出文件说明

### 1. 股票池缓存 `stock_universe.json`

示例：

```json
{
  "updated_at": "2026-05-03 16:07:05",
  "expires_at": "2026-05-04 16:07:05",
  "stock_count": 5512,
  "stocks": [
    {
      "symbol": "000001",
      "stock_name": "平安银行"
    }
  ]
}
```

### 2. 分红缓存 `stock_dividend_cache.json`

示例：

```json
{
  "updated_at": "2026-05-03 16:07:05",
  "expires_at": "2026-05-04 16:07:05",
  "stock_count": 5512,
  "data": {
    "600036": {
      "ttm_dividend": 3.013,
      "updated_at": "2026-05-03 16:07:05"
    },
    "000651": {
      "ttm_dividend": 4.0,
      "updated_at": "2026-05-03 16:07:05"
    }
  }
}
```

### 3. 价格缓存 `stock_price_cache.json`

示例：

```json
{
  "updated_at": "2026-05-03 17:10:05",
  "expires_at": "2026-05-04 17:10:05",
  "stock_count": 5512,
  "data": {
    "000065": {
      "current_price": 12.79,
      "updated_at": "2026-05-03 17:10:05"
    },
    "600036": {
      "current_price": 38.27,
      "updated_at": "2026-05-03 17:10:05"
    }
  }
}
```

价格写入逻辑：

- 优先使用批量行情接口返回的 `最新价`
- 如果 `最新价` 无效，则回退使用 `昨收`
- 如果批量结果里缺失某只股票，则尝试复用旧缓存

### 4. 指数成分股缓存 `index_constituents/000922.json`

示例：

```json
{
  "index_code": "000922",
  "index_name": "中证红利",
  "updated_at": "2026-05-03 16:07:05",
  "expires_at": "2026-05-10 16:07:05",
  "stock_count": 100,
  "stocks": [
    {
      "symbol": "000090",
      "stock_name": "天健集团",
      "included_date": "2021-12-13"
    }
  ]
}
```

### 5. 指数详情结果 `index_000922_dividend_yield.json`

结构如下：

```json
{
  "index_info": {
    "index_code": "000922",
    "index_name": "中证红利",
    "updated_at": "2026-05-03 17:10:40",
    "stock_count": 100,
    "avg_yield": 4.66,
    "median_yield": 4.38,
    "max_yield": 11.26,
    "min_yield": 0.0
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

### 6. 首页索引 `indexes.json`

结构如下：

```json
[
  {
    "index_code": "000922",
    "index_name": "中证红利",
    "file": "index_000922_dividend_yield.json",
    "stock_count": 100,
    "avg_yield": 4.66,
    "median_yield": 4.38,
    "max_yield": 11.26,
    "min_yield": 0.0,
    "updated_at": "2026-05-03 17:10:40"
  }
]
```

### 7. 原始分红数据缓存 `stock_dividend_raw/000001.json`（新增）

保存单只股票的完整历史分红记录，结构如下：

```json
{
  "symbol": "000001",
  "updated_at": "2026-05-05 12:02:42",
  "expires_at": "2026-06-04 12:02:42",
  "record_count": 27,
  "records": [
    {
      "announce_date": "1992-03-14",
      "dividend_type": "年度分红",
      "dividend_per_10_shares": 2.0,
      "bonus_share_per_10_shares": 0.0,
      "transfer_share_per_10_shares": 5.0,
      "record_date": "1992-03-20",
      "ex_date": "1992-03-23",
      "payment_date": "NaT",
      "dividend_per_share": 0.2,
      "bonus_share_ratio": 0.0,
      "transfer_share_ratio": 0.5
    }
  ],
  "summary": {
    "first_dividend_year": 1992,
    "latest_dividend_date": "1992-03-23",
    "total_years_with_dividend": 25
  }
}
```

### 8. 股票历史分红汇总 `stock_dividend_history/000001.json`（新增）

基于原始分红数据生成的统计汇总，结构如下：

```json
{
  "symbol": "000001",
  "stock_name": "平安银行",
  "generated_at": "2026-05-05 12:02:42",
  "dividend_summary": {
    "total_records": 27,
    "first_dividend_year": 1992,
    "latest_dividend_date": "2025-10-16",
    "consecutive_years": 25
  },
  "statistics": {
    "all_time": {
      "total_dividend_per_share": 45.67,
      "avg_annual_dividend": 1.90,
      "max_annual_dividend": 7.90,
      "min_annual_dividend": 0.50
    },
    "recent_5y": {
      "total_dividend_per_share": 12.5,
      "avg_annual_dividend": 2.50
    },
    "recent_10y": {
      "total_dividend_per_share": 28.3,
      "avg_annual_dividend": 2.83
    }
  },
  "annual_dividends": [
    {
      "year": 2025,
      "total_dividend": 5.1,
      "times": 2,
      "details": [
        {"date": "2025-10-16", "type": "中期", "amount": 2.1},
        {"date": "2025-08-08", "type": "年度", "amount": 3.0}
      ]
    }
  ],
  "raw_data_ref": "../../cache/stock_dividend_raw/000001.json"
}
```

### 9. 全市场分红汇总 `stock_dividend_summary.json`（新增）

全市场分红统计汇总，结构如下：

```json
{
  "generated_at": "2026-05-05 12:30:00",
  "stock_count": 5342,
  "top_dividend_stocks": [
    {
      "symbol": "000001",
      "stock_name": "平安银行",
      "total_dividend": 45.67,
      "avg_annual": 1.90,
      "consecutive_years": 25
    }
  ],
  "statistics": {
    "dividend_paying_stocks": 4200,
    "non_dividend_stocks": 1142
  }
}
```

## AkShare 主要函数说明

当前脚本主要使用 4 个 `AkShare` 函数。

### 1. `ak.stock_info_a_code_name()`

功能：

- 获取沪深京 A 股股票列表

返回结果的典型形态：

```text
    code    name
0  000001  平安银行
1  000002   万科A
```

脚本实际使用的字段：

- `code`
- `name`

脚本中的用途：

- 构造全 A 股股票池缓存
- `code` 经过 `normalize_symbol()` 后写入 `symbol`
- `name` 写入 `stock_name`

对应代码：

- [main.py](F:\Desktop\AI-Code\DiviQuant\main.py:113)

### 2. `ak.index_stock_cons(symbol=...)`

功能：

- 获取指定指数的最新成分股列表

返回结果的典型形态：

```text
      品种代码  品种名称      纳入日期
0     000090  天健集团  2021-12-13
1     000157  中联重科  2013-01-04
```

脚本实际使用的字段：

- `品种代码`
- `品种名称`
- `纳入日期`

脚本中的用途：

- 构造指数成分股缓存
- 生成指数详情页里的 `stock_name` 和 `included_date`

对应代码：

- [main.py](F:\Desktop\AI-Code\DiviQuant\main.py:142)

### 3. `ak.stock_dividend_cninfo(symbol=...)`

功能：

- 获取单只股票在巨潮资讯上的历史分红记录

脚本关注的典型字段：

```text
    派息比例      除权日
0    30.13  2025-07-10
1    17.38  2024-07-11
```

脚本实际使用的字段：

- `派息比例`
- `除权日`

脚本中的用途：

1. 将 `派息比例` 转换为 `每股分红`
2. 将 `除权日` 转为日期
3. 过滤最近 365 天记录
4. 求和得到 `ttm_dividend`

公式：

```text
每股分红 = 派息比例 / 10
ttm_dividend = 最近 365 天每次每股分红之和
```

对应代码：

- [dividend_data_generator.py](F:\Desktop\AI-Code\DiviQuant\web\scripts\dividend_data_generator.py:93)

### 4. `ak.stock_zh_a_spot()`

功能：

- 获取新浪财经全市场 A 股实时行情

返回结果的典型形态：

```text
         代码    名称    最新价     昨收
0  sz000065  北方国际  12.79  12.65
1  sh600036  招商银行  38.27  37.95
2  bj920000  安徽凤凰  15.73  15.69
```

脚本实际使用的字段：

- `代码`
- `最新价`
- `昨收`

脚本中的用途：

- 一次性获取全市场最新价格
- `代码` 经过 `normalize_symbol()` 后与股票池对齐
- 优先使用 `最新价`
- 如果 `最新价` 无效，则回退使用 `昨收`
- 最终写入 `current_price`

对应代码：

- [dividend_data_generator.py](F:\Desktop\AI-Code\DiviQuant\web\scripts\dividend_data_generator.py:215)

注意：

- 这个接口虽然是批量接口，但并不是“瞬时返回”，一次全市场抓取通常仍需几十秒
- 好处是它比逐只调用历史行情接口快得多

## 关键计算逻辑

### 1. TTM 分红

公式：

```text
ttm_dividend = 最近 365 天每次分红的每股分红之和
```

### 2. 股息率

公式：

```text
ttm_yield = ttm_dividend / current_price * 100
```

示例：

```text
ttm_dividend = 1.59
current_price = 14.12
ttm_yield = 11.26%
```

## 脚本内部函数职责

### 目录与缓存基础

- `ensure_directories()`
  创建缓存和派生结果目录
- `load_json()`
  读取 JSON 文件
- `save_json()`
  保存 JSON 文件
- `is_cache_valid()`
  判断缓存是否过期
- `normalize_symbol()`
  统一股票代码格式

### 原始数据抓取

- `refresh_stock_universe()`
  刷新或读取全 A 股股票池
- `refresh_index_constituents()`
  刷新或读取指数成分股
- `refresh_dividend_raw_cache()`（新增）
  获取并缓存单只股票的完整分红历史
- `get_ttm_dividend()`
  计算单只股票最近 12 个月的每股分红
- `refresh_metric_cache()`
  刷新分红类逐股缓存
- `refresh_price_cache()`
  使用批量行情接口刷新全市场价格缓存

### 分红数据处理（新增）

- `build_stock_dividend_history()`
  基于原始分红数据生成历史汇总，包括：
  - 按年度统计分红金额和次数
  - 计算历史统计指标（总计/平均/最高/最低）
  - 近5年/近10年分红统计
- `save_stock_dividend_history()`
  保存单只股票历史分红汇总
- `build_dividend_summary()`
  生成全市场分红统计汇总，包括：
  - Top 100 分红股票排行
  - 分红股票数量统计

### 指标合成与结果输出

- `build_stock_metrics()`
  合并分红缓存和价格缓存
- `build_index_dataframe()`
  从全市场指标中筛出某个指数的股票
- `build_index_payload()`
  生成前端使用的详情 JSON
- `save_index_payload()`
  保存单个指数 JSON
- `save_indexes_summary()`
  保存首页 `indexes.json`

## 当前已配置指数

在 [dividend_data_generator.py](F:\Desktop\AI-Code\DiviQuant\web\scripts\dividend_data_generator.py:19) 中配置：

- `000922` 中证红利
- `000015` 上证红利
- `399324` 深证红利
- `000300` 沪深300

## 运行方式

```bash
python dividend_data_generator.py
```

首次运行特点：

- 会抓取全 A 股股票池
- 会逐只计算全 A 股分红
- 会批量抓取全市场价格
- 会生成所有指数的派生 JSON

后续运行特点：

- 如果缓存未过期，会直接复用缓存
- 速度会明显快很多

## 注意事项

### 1. 数据源组成

当前脚本使用的数据源：

- 股票池：A 股列表接口
- 指数成分股：新浪指数成分股接口
- 分红：巨潮资讯历史分红接口
- 价格：新浪批量实时行情接口

### 2. 价格接口替换说明

旧版本价格获取方式：

- 逐只调用 `ak.stock_zh_a_hist_tx()`
- 适合单只股票历史行情
- 不适合全市场最新价获取

当前版本价格获取方式：

- 使用 `ak.stock_zh_a_spot()` 一次性获取全市场行情
- 再按标准化后的股票代码对齐股票池

这样做的主要收益：

- 避免对全 A 股逐只拉历史行情
- 明显减少请求次数
- 大幅缩短价格层刷新时间

### 3. 中文乱码

如果在 Windows PowerShell 中看到中文乱码，通常是终端显示编码问题，不代表 JSON 文件本身编码异常。

JSON 文件均按 `UTF-8` 保存，网页读取不会受影响。

### 4. 首次全量跑数仍然不算很快

这是预期行为，原因有两个：

- 分红数据仍然需要按股票逐只计算并缓存
- 新浪批量行情接口虽然比逐只历史行情快，但全市场抓取仍需几十秒

### 5. 某些股票的股息率可能为 0

出现这种情况通常是：

- 最近 365 天没有有效分红记录
- 或分红接口未返回可用值

这不一定代表脚本错误。

## 后续建议

- 给脚本增加命令行参数，例如 `--force-refresh`
- 支持单独刷新某类缓存，例如只刷新价格缓存
- 给派生结果增加数据日期字段
- 前端开发时直接读取 `output/derived/indexes.json` 和各指数详情 JSON

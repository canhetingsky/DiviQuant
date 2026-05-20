import json
from datetime import datetime, timedelta
from pathlib import Path

import akshare as ak
import pandas as pd


OUTPUT_DIR = Path(__file__).parent / "output"
CACHE_DIR = OUTPUT_DIR / "cache"
DERIVED_DIR = OUTPUT_DIR / "derived"
INDEX_CACHE_DIR = CACHE_DIR / "index_constituents"
DIVIDEND_RAW_CACHE_DIR = CACHE_DIR / "stock_dividend_raw"
DIVIDEND_HISTORY_DIR = DERIVED_DIR / "stock_dividend_history"

STOCK_UNIVERSE_TTL_HOURS = 24
DIVIDEND_CACHE_TTL_HOURS = 24
DIVIDEND_RAW_TTL_HOURS = 24 * 30
PRICE_CACHE_TTL_HOURS = 24
INDEX_CONSTITUENTS_TTL_HOURS = 24 * 7

INDEX_CONFIGS = [
    {"index_code": "000922", "index_name": "中证红利"},
    {"index_code": "000015", "index_name": "上证红利"},
    {"index_code": "399324", "index_name": "深证红利"},
    {"index_code": "000300", "index_name": "沪深300"},
    {"index_code": "H30269", "index_name": "红利低波指数"},
]


def ensure_directories() -> None:
    """Create output directories used by caches and derived files."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def now() -> datetime:
    """Return the current local time."""
    return datetime.now()


def format_dt(value: datetime) -> str:
    """Serialize datetime as a stable string."""
    return value.strftime("%Y-%m-%d %H:%M:%S")


def parse_dt(value: str | None) -> datetime | None:
    """Parse serialized datetime values from cache files."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def build_expiry(hours: int) -> str:
    """Build an expires_at string from a ttl value."""
    return format_dt(now() + timedelta(hours=hours))


def is_cache_valid(payload: dict | None) -> bool:
    """Check whether a cache payload is still within its validity period."""
    if not payload:
        return False
    expires_at = parse_dt(payload.get("expires_at"))
    if expires_at is None:
        return False
    return now() < expires_at


def load_json(path: Path) -> dict | list | None:
    """Read JSON from disk when available."""
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: dict | list) -> None:
    """Persist JSON using UTF-8 without ASCII escaping."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False,
                    indent=2), encoding="utf-8")


def normalize_symbol(value: str) -> str:
    """Normalize stock codes to 6-digit strings."""
    text = str(value).strip().lower()
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) >= 6:
        return digits[-6:]
    return digits.zfill(6)


def refresh_dividend_raw_cache(symbol: str, force: bool = False) -> dict:
    """获取单只股票完整分红历史并缓存."""
    cache_path = DIVIDEND_RAW_CACHE_DIR / f"{symbol}.json"
    cached = load_json(cache_path)

    if not force and isinstance(cached, dict) and is_cache_valid(cached):
        return cached

    try:
        df = ak.stock_dividend_cninfo(symbol=symbol)
        records = []

        for row in df.itertuples(index=False):
            record = {
                "announce_date": str(row[0]) if len(row) > 0 and row[0] else None,
                "dividend_type": str(row[1]) if len(row) > 1 and row[1] else None,
                "bonus_share_per_10_shares": float(row[2]) if len(row) > 2 and pd.notna(row[2]) else None,
                "transfer_share_per_10_shares": float(row[3]) if len(row) > 3 and pd.notna(row[3]) else None,
                "dividend_per_10_shares": float(row[4]) if len(row) > 4 and pd.notna(row[4]) else None,
                "record_date": str(row[5]) if len(row) > 5 and row[5] else None,
                "ex_date": str(row[6]) if len(row) > 6 and row[6] else None,
                "payment_date": str(row[7]) if len(row) > 7 and row[7] else None,
                "share_arrival_date": str(row[8]) if len(row) > 8 and row[8] else None,
                "description": str(row[9]) if len(row) > 9 and row[9] else None,
                "dividend_per_share": round(float(row[4]) / 10, 4) if len(row) > 4 and pd.notna(row[4]) else 0.0,
                "bonus_share_ratio": round(float(row[2]) / 10, 4) if len(row) > 2 and pd.notna(row[2]) else 0.0,
                "transfer_share_ratio": round(float(row[3]) / 10, 4) if len(row) > 3 and pd.notna(row[3]) else 0.0,
            }
            records.append(record)

        years = set()
        for r in records:
            if r["ex_date"]:
                try:
                    years.add(int(r["ex_date"][:4]))
                except:
                    pass

        payload = {
            "symbol": symbol,
            "updated_at": format_dt(now()),
            "expires_at": build_expiry(DIVIDEND_RAW_TTL_HOURS),
            "record_count": len(records),
            "records": records,
            "summary": {
                "first_dividend_year": min(years) if years else None,
                "latest_dividend_date": records[0]["ex_date"] if records else None,
                "total_years_with_dividend": len(years)
            }
        }
        save_json(cache_path, payload)
        return payload

    except Exception as e:
        # 对于无分红数据的股票，akshare会抛出KeyError，这是正常情况
        error_msg = str(e)
        if "实施方案公告日期" in error_msg or "派息比例" in error_msg:
            # 无分红数据，返回空记录（使用正常TTL，因为这类股票确实没有分红）
            payload = {
                "symbol": symbol,
                "updated_at": format_dt(now()),
                "expires_at": build_expiry(DIVIDEND_RAW_TTL_HOURS),
                "record_count": 0,
                "records": [],
                "summary": {
                    "first_dividend_year": None,
                    "latest_dividend_date": None,
                    "total_years_with_dividend": 0
                },
                "note": "该股票无分红记录"
            }
            save_json(cache_path, payload)
            return payload
        else:
            # 其他错误，使用短TTL重试
            print(f"获取 {symbol} 分红数据失败: {e}")
            return {
                "symbol": symbol,
                "updated_at": format_dt(now()),
                "expires_at": build_expiry(1),
                "record_count": 0,
                "records": [],
                "error": str(e)
            }


def get_ttm_dividend(symbol: str) -> float:
    """Calculate per-share dividends paid during the trailing 12 months."""
    raw_data = refresh_dividend_raw_cache(symbol)
    records = raw_data.get("records", [])

    if not records:
        return 0.0

    end_date = now()
    start_date = end_date - timedelta(days=365)

    total = 0.0
    for r in records:
        ex_date_str = r.get("ex_date")
        if not ex_date_str:
            continue
        try:
            ex_date = datetime.strptime(ex_date_str, "%Y-%m-%d")
            if start_date <= ex_date <= end_date:
                total += r.get("dividend_per_share", 0.0)
        except ValueError:
            continue

    return round(total, 4)


def refresh_stock_universe(force: bool = False) -> list[dict]:
    """Load or refresh the full A-share universe."""
    cache_path = CACHE_DIR / "stock_universe.json"
    cached_payload = load_json(cache_path)
    if not force and isinstance(cached_payload, dict) and is_cache_valid(cached_payload):
        return cached_payload["stocks"]

    print("正在刷新全 A 股股票池...")
    df = ak.stock_info_a_code_name()
    df["code"] = df["code"].apply(normalize_symbol)
    df = df.drop_duplicates(subset=["code"], keep="last").sort_values(
        "code").reset_index(drop=True)

    stocks = [
        {"symbol": row.code, "stock_name": row.name}
        for row in df.itertuples(index=False)
    ]

    payload = {
        "updated_at": format_dt(now()),
        "expires_at": build_expiry(STOCK_UNIVERSE_TTL_HOURS),
        "stock_count": len(stocks),
        "stocks": stocks,
    }
    save_json(cache_path, payload)
    return stocks


def refresh_index_constituents(index_code: str, index_name: str, force: bool = False) -> list[dict]:
    """Load or refresh a cached list of index constituents."""
    cache_path = INDEX_CACHE_DIR / f"{index_code}.json"
    cached_payload = load_json(cache_path)
    if not force and isinstance(cached_payload, dict) and is_cache_valid(cached_payload):
        return cached_payload["stocks"]

    print(f"正在刷新指数 {index_code} {index_name} 的成分股...")
    df = ak.index_stock_cons(symbol=index_code)
    df["品种代码"] = df["品种代码"].apply(normalize_symbol)
    df = df.drop_duplicates(subset=["品种代码"], keep="last").sort_values(
        "品种代码").reset_index(drop=True)

    stocks = []
    for row in df.itertuples(index=False):
        stocks.append(
            {
                "symbol": row.品种代码,
                "stock_name": row.品种名称,
                "included_date": str(row.纳入日期) if pd.notna(row.纳入日期) else "",
            }
        )

    payload = {
        "index_code": index_code,
        "index_name": index_name,
        "updated_at": format_dt(now()),
        "expires_at": build_expiry(INDEX_CONSTITUENTS_TTL_HOURS),
        "stock_count": len(stocks),
        "stocks": stocks,
    }
    save_json(cache_path, payload)
    print(f"共获取到 {len(stocks)} 只成分股")
    return stocks


def refresh_metric_cache(
    cache_name: str,
    ttl_hours: int,
    symbols: list[str],
    fetcher,
    value_field: str,
    force: bool = False,
) -> dict[str, dict]:
    """Load or refresh a per-symbol metric cache."""
    cache_path = CACHE_DIR / cache_name
    cached_payload = load_json(cache_path)
    if not force and isinstance(cached_payload, dict) and is_cache_valid(cached_payload):
        return cached_payload["data"]

    refreshed_at = format_dt(now())
    cached_data = cached_payload.get(
        "data", {}) if isinstance(cached_payload, dict) else {}
    data: dict[str, dict] = {}
    total = len(symbols)

    print(f"开始刷新 {cache_name}，共 {total} 只股票")
    for index, symbol in enumerate(symbols, 1):
        print(f"[{index}/{total}] 正在抓取 {symbol}...", end="\r")
        value = fetcher(symbol)
        item = {
            value_field: value,
            "updated_at": refreshed_at,
        }
        if value is None and symbol in cached_data:
            previous_item = cached_data[symbol]
            item = {
                value_field: previous_item.get(value_field),
                "updated_at": previous_item.get("updated_at", refreshed_at),
                "stale_fallback": True,
            }
        data[symbol] = item

    print()
    payload = {
        "updated_at": refreshed_at,
        "expires_at": build_expiry(ttl_hours),
        "stock_count": len(data),
        "data": data,
    }
    save_json(cache_path, payload)
    return data


def refresh_price_cache(stock_universe: list[dict], force: bool = False) -> dict[str, dict]:
    """Load or refresh the full-market latest price cache with a batch quote API."""
    cache_path = CACHE_DIR / "stock_price_cache.json"
    cached_payload = load_json(cache_path)
    if not force and isinstance(cached_payload, dict) and is_cache_valid(cached_payload):
        cached_data = cached_payload["data"]
        has_valid_price = any(
            item.get("current_price") is not None for item in cached_data.values()
        )
        if has_valid_price:
            return cached_data

    refreshed_at = format_dt(now())
    cached_data = cached_payload.get(
        "data", {}) if isinstance(cached_payload, dict) else {}

    print("开始刷新 stock_price_cache.json，使用批量行情接口获取全市场最新价")
    spot_df = ak.stock_zh_a_spot()
    spot_df["代码"] = spot_df["代码"].apply(normalize_symbol)

    data: dict[str, dict] = {}
    universe_symbols = {stock["symbol"] for stock in stock_universe}

    for row in spot_df.itertuples(index=False):
        symbol = normalize_symbol(row.代码)
        if symbol not in universe_symbols:
            continue

        latest_price = pd.to_numeric(row.最新价, errors="coerce")
        prev_close = pd.to_numeric(row.昨收, errors="coerce")
        chosen_price = latest_price
        if pd.isna(chosen_price) or chosen_price <= 0:
            chosen_price = prev_close

        data[symbol] = {
            "current_price": round(float(chosen_price), 4) if pd.notna(chosen_price) and chosen_price > 0 else None,
            "updated_at": refreshed_at,
        }

    for symbol in universe_symbols:
        if symbol not in data:
            previous_item = cached_data.get(symbol, {})
            data[symbol] = {
                "current_price": previous_item.get("current_price"),
                "updated_at": previous_item.get("updated_at", refreshed_at),
                "stale_fallback": True,
            }

    payload = {
        "updated_at": refreshed_at,
        "expires_at": build_expiry(PRICE_CACHE_TTL_HOURS),
        "stock_count": len(data),
        "data": data,
    }
    save_json(cache_path, payload)
    return data


def build_stock_metrics(
    stock_universe: list[dict],
    dividend_cache: dict[str, dict],
    price_cache: dict[str, dict],
) -> dict[str, dict]:
    """Merge full-market dividend and price caches into a stock metrics map."""
    metrics: dict[str, dict] = {}
    for stock in stock_universe:
        symbol = stock["symbol"]
        dividend_value = dividend_cache.get(symbol, {}).get("ttm_dividend")
        price_value = price_cache.get(symbol, {}).get("current_price")

        if price_value is None or price_value <= 0:
            continue

        ttm_dividend = round(float(dividend_value or 0.0), 2)
        current_price = round(float(price_value), 2)
        ttm_yield = round((ttm_dividend / current_price) * 100, 2)

        metrics[symbol] = {
            "symbol": symbol,
            "stock_name": stock.get("stock_name", ""),
            "current_price": current_price,
            "ttm_dividend": ttm_dividend,
            "ttm_yield": ttm_yield,
        }

    return metrics


def build_all_stocks_yield(stock_metrics: dict[str, dict]) -> dict:
    """Build all stocks dividend yield data for frontend display."""
    stocks_list = list(stock_metrics.values())

    # 按股息率降序排序
    stocks_list.sort(key=lambda x: x["ttm_yield"], reverse=True)

    # 添加排名
    for idx, stock in enumerate(stocks_list, 1):
        stock["rank"] = idx

    # 计算统计数据
    yields = [s["ttm_yield"] for s in stocks_list if s["ttm_yield"] > 0]
    dividend_paying_count = len(yields)

    return {
        "generated_at": format_dt(now()),
        "total_stocks": len(stocks_list),
        "dividend_paying_stocks": dividend_paying_count,
        "non_dividend_stocks": len(stocks_list) - dividend_paying_count,
        "statistics": {
            "avg_yield": round(sum(yields) / len(yields), 2) if yields else 0,
            "median_yield": round(sorted(yields)[len(yields) // 2], 2) if yields else 0,
            "max_yield": round(max(yields), 2) if yields else 0,
            "min_yield": round(min(yields), 2) if yields else 0,
        },
        "stocks": stocks_list,
    }


def build_stock_dividend_history(symbol: str, raw_data: dict, stock_name: str = "") -> dict:
    """基于原始分红数据生成历史汇总."""
    records = raw_data.get("records", [])

    annual_data = {}
    for r in records:
        if not r.get("ex_date"):
            continue
        try:
            year = int(r["ex_date"][:4])
        except:
            continue
        if year not in annual_data:
            annual_data[year] = {"total": 0.0, "times": 0, "details": []}

        annual_data[year]["total"] += r.get("dividend_per_share", 0)
        annual_data[year]["times"] += 1
        annual_data[year]["details"].append({
            "date": r["ex_date"],
            "type": r.get("dividend_type", ""),
            "amount": r.get("dividend_per_share", 0)
        })

    yearly_totals = [d["total"] for d in annual_data.values()]
    recent_5y = yearly_totals[-5:] if len(
        yearly_totals) >= 5 else yearly_totals
    recent_10y = yearly_totals[-10:] if len(
        yearly_totals) >= 10 else yearly_totals

    return {
        "symbol": symbol,
        "stock_name": stock_name,
        "generated_at": format_dt(now()),
        "dividend_summary": {
            "total_records": len(records),
            "first_dividend_year": raw_data.get("summary", {}).get("first_dividend_year"),
            "latest_dividend_date": raw_data.get("summary", {}).get("latest_dividend_date"),
            "consecutive_years": len(annual_data),
        },
        "statistics": {
            "all_time": {
                "total_dividend_per_share": round(sum(yearly_totals), 4),
                "avg_annual_dividend": round(sum(yearly_totals) / len(yearly_totals), 4) if yearly_totals else 0,
                "max_annual_dividend": round(max(yearly_totals), 4) if yearly_totals else 0,
                "min_annual_dividend": round(min(yearly_totals), 4) if yearly_totals else 0,
            },
            "recent_5y": {
                "total_dividend_per_share": round(sum(recent_5y), 4),
                "avg_annual_dividend": round(sum(recent_5y) / len(recent_5y), 4) if recent_5y else 0,
            },
            "recent_10y": {
                "total_dividend_per_share": round(sum(recent_10y), 4),
                "avg_annual_dividend": round(sum(recent_10y) / len(recent_10y), 4) if recent_10y else 0,
            }
        },
        "annual_dividends": [
            {
                "year": year,
                "total_dividend": round(data["total"], 4),
                "times": data["times"],
                "details": data["details"]
            }
            for year, data in sorted(annual_data.items(), reverse=True)
        ],
        "raw_data_ref": f"../../cache/stock_dividend_raw/{symbol}.json"
    }


def save_stock_dividend_history(symbol: str, history: dict) -> Path:
    """保存股票历史分红汇总."""
    path = DIVIDEND_HISTORY_DIR / f"{symbol}.json"
    save_json(path, history)
    return path


def build_dividend_summary(stock_universe: list[dict]) -> dict:
    """生成全市场分红统计汇总."""
    histories = []
    for stock in stock_universe:
        symbol = stock["symbol"]
        path = DIVIDEND_HISTORY_DIR / f"{symbol}.json"
        if path.exists():
            data = load_json(path)
            if data:
                histories.append({
                    "symbol": symbol,
                    "stock_name": stock.get("stock_name", ""),
                    "total_dividend": data.get("statistics", {}).get("all_time", {}).get("total_dividend_per_share", 0),
                    "avg_annual": data.get("statistics", {}).get("all_time", {}).get("avg_annual_dividend", 0),
                    "consecutive_years": data.get("dividend_summary", {}).get("consecutive_years", 0),
                })

    histories.sort(key=lambda x: x["total_dividend"], reverse=True)

    return {
        "generated_at": format_dt(now()),
        "stock_count": len(stock_universe),
        "top_dividend_stocks": histories[:100],
        "statistics": {
            "dividend_paying_stocks": len([h for h in histories if h["total_dividend"] > 0]),
            "non_dividend_stocks": len(stock_universe) - len([h for h in histories if h["total_dividend"] > 0]),
        }
    }


def build_index_dataframe(constituents: list[dict], stock_metrics: dict[str, dict]) -> pd.DataFrame:
    """Build a sorted dataframe for one index from full-market cached metrics."""
    rows = []
    total = len(constituents)
    for index, stock in enumerate(constituents, 1):
        symbol = stock["symbol"]
        print(f"[{index}/{total}] 正在生成 {symbol}...", end="\r")
        metric = stock_metrics.get(symbol)
        if not metric:
            continue

        rows.append(
            {
                "symbol": symbol,
                "stock_name": stock.get("stock_name") or metric.get("stock_name", ""),
                "included_date": stock.get("included_date", ""),
                "current_price": metric["current_price"],
                "ttm_dividend": metric["ttm_dividend"],
                "ttm_yield": metric["ttm_yield"],
            }
        )

    print()
    if not rows:
        return pd.DataFrame(
            columns=[
                "symbol",
                "stock_name",
                "included_date",
                "current_price",
                "ttm_dividend",
                "ttm_yield",
            ]
        )

    df = pd.DataFrame(rows)
    return df.sort_values("ttm_yield", ascending=False).reset_index(drop=True)


def build_index_payload(index_code: str, index_name: str, df: pd.DataFrame) -> dict:
    """Convert an index dataframe into the frontend JSON schema."""
    generated_at = format_dt(now())
    stock_count = int(len(df))

    if df.empty:
        avg_yield = median_yield = max_yield = min_yield = 0.0
    else:
        avg_yield = round(float(df["ttm_yield"].mean()), 2)
        median_yield = round(float(df["ttm_yield"].median()), 2)
        max_yield = round(float(df["ttm_yield"].max()), 2)
        min_yield = round(float(df["ttm_yield"].min()), 2)

    return {
        "index_info": {
            "index_code": index_code,
            "index_name": index_name,
            "updated_at": generated_at,
            "stock_count": stock_count,
            "avg_yield": avg_yield,
            "median_yield": median_yield,
            "max_yield": max_yield,
            "min_yield": min_yield,
        },
        "stocks": df.to_dict(orient="records"),
    }


def save_index_payload(payload: dict) -> dict:
    """Write a single index detail file and return its summary row."""
    index_info = payload["index_info"]
    index_code = index_info["index_code"]
    json_path = DERIVED_DIR / f"index_{index_code}_dividend_yield.json"
    save_json(json_path, payload)

    print(f"JSON 结果已保存到: {json_path}")
    return {
        "index_code": index_info["index_code"],
        "index_name": index_info["index_name"],
        "file": json_path.name,
        "stock_count": index_info["stock_count"],
        "avg_yield": index_info["avg_yield"],
        "median_yield": index_info["median_yield"],
        "max_yield": index_info["max_yield"],
        "min_yield": index_info["min_yield"],
        "updated_at": index_info["updated_at"],
    }


def save_indexes_summary(summaries: list[dict]) -> Path:
    """Write the index summary file used by the overview page."""
    indexes_path = DERIVED_DIR / "indexes.json"
    save_json(indexes_path, summaries)
    return indexes_path


def print_index_summary(payload: dict, df: pd.DataFrame) -> None:
    """Print a concise console summary for one index."""
    index_info = payload["index_info"]
    print("\n" + "=" * 80)
    print(
        f"指数 {index_info['index_code']} {index_info['index_name']} 成分股股息率排名（前20）")
    print("=" * 80)
    print(df.head(20).to_string(index=True))

    print("\n" + "=" * 80)
    print("统计摘要")
    print("=" * 80)
    print(f"成功生成数据: {index_info['stock_count']} 只股票")
    print(f"平均股息率: {index_info['avg_yield']:.2f}%")
    print(f"最高股息率: {index_info['max_yield']:.2f}%")
    print(f"最低股息率: {index_info['min_yield']:.2f}%")
    print(f"中位数股息率: {index_info['median_yield']:.2f}%")


def main() -> None:
    ensure_directories()

    # 确保新目录存在
    DIVIDEND_RAW_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    DIVIDEND_HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    stock_universe = refresh_stock_universe()
    all_symbols = [stock["symbol"] for stock in stock_universe]

    index_constituents_map: dict[str, list[dict]] = {}
    for config in INDEX_CONFIGS:
        index_constituents_map[config["index_code"]] = refresh_index_constituents(
            config["index_code"], config["index_name"]
        )

    dividend_cache = refresh_metric_cache(
        cache_name="stock_dividend_cache.json",
        ttl_hours=DIVIDEND_CACHE_TTL_HOURS,
        symbols=all_symbols,
        fetcher=get_ttm_dividend,
        value_field="ttm_dividend",
    )
    price_cache = refresh_price_cache(stock_universe=stock_universe)
    stock_metrics = build_stock_metrics(
        stock_universe, dividend_cache, price_cache)

    # 生成每只股票的历史分红汇总
    print("\n" + "#" * 80)
    print("开始生成股票历史分红汇总")
    print("#" * 80)
    total = len(stock_universe)
    for idx, stock in enumerate(stock_universe, 1):
        symbol = stock["symbol"]
        stock_name = stock.get("stock_name", "")
        print(f"[{idx}/{total}] 处理 {symbol} {stock_name}...", end="\r")

        # 获取原始分红数据（使用已缓存的数据）
        raw_data = refresh_dividend_raw_cache(symbol)

        # 生成历史汇总
        history = build_stock_dividend_history(symbol, raw_data, stock_name)

        # 保存
        save_stock_dividend_history(symbol, history)

    print(f"\n完成 {total} 只股票的历史分红汇总生成")

    # 生成全市场分红汇总
    print("\n生成全市场分红统计汇总...")
    summary = build_dividend_summary(stock_universe)
    summary_path = DERIVED_DIR / "stock_dividend_summary.json"
    save_json(summary_path, summary)
    print(f"全市场分红汇总已保存到: {summary_path}")

    # 生成全市场股票股息率数据
    print("\n生成全市场股票股息率数据...")
    all_stocks_yield = build_all_stocks_yield(stock_metrics)
    all_stocks_path = DERIVED_DIR / "all_stocks_dividend_yield.json"
    save_json(all_stocks_path, all_stocks_yield)
    print(f"全市场股票股息率数据已保存到: {all_stocks_path}")

    summaries = []
    for config in INDEX_CONFIGS:
        print("\n" + "#" * 80)
        print(f"开始生成指数结果 {config['index_code']} {config['index_name']}")
        print("#" * 80)
        df = build_index_dataframe(
            index_constituents_map[config["index_code"]], stock_metrics)
        payload = build_index_payload(
            config["index_code"], config["index_name"], df)
        print_index_summary(payload, df)
        summaries.append(save_index_payload(payload))

    indexes_path = save_indexes_summary(summaries)
    print(f"\n首页索引文件已保存到: {indexes_path}")


if __name__ == "__main__":
    main()

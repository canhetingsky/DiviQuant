import dayjs from "dayjs";

// 从环境变量获取数据 API 基础地址
const DATA_BASE_URL = import.meta.env.VITE_DATA_BASE_URL || "https://development.s3.bitiful.net/DiviQuant";

export async function fetchIndexes() {
  const response = await fetch(`${DATA_BASE_URL}/indexes.json`);
  if (!response.ok) throw new Error("Failed to fetch indexes");
  return response.json();
}

export async function fetchIndexDetail(filename) {
  const response = await fetch(`${DATA_BASE_URL}/${filename}`);
  if (!response.ok) throw new Error(`Failed to fetch ${filename}`);
  return response.json();
}

export async function fetchStockDividendSummary() {
  const response = await fetch(`${DATA_BASE_URL}/stock_dividend_summary.json`);
  if (!response.ok) throw new Error("Failed to fetch stock dividend summary");
  return response.json();
}

export async function fetchAllStocksYield() {
  const response = await fetch(
    `${DATA_BASE_URL}/all_stocks_dividend_yield.json`,
  );
  if (!response.ok) throw new Error("Failed to fetch all stocks yield");
  return response.json();
}

export function formatYield(value) {
  if (value == null || value === 0) return "--";
  return `${value.toFixed(2)}%`;
}

export function formatPrice(value) {
  if (value == null) return "--";
  return value.toFixed(2);
}

export function formatDate(dateStr) {
  if (!dateStr) return "--";
  return dayjs(dateStr).format("YYYY-MM-DD HH:mm");
}

export function formatDateShort(dateStr) {
  if (!dateStr) return "--";
  return dayjs(dateStr).format("YYYY-MM-DD");
}

export function getYieldClass(value) {
  if (value == null || value === 0) return "text-slate-400";
  if (value >= 5) return "text-emerald-600 font-semibold";
  if (value >= 3) return "text-slate-700";
  return "text-rose-600";
}

export function sortIndexes(indexes, sortBy, order) {
  return [...indexes].sort((a, b) => {
    let valA = a[sortBy];
    let valB = b[sortBy];
    if (order === "asc") {
      return valA - valB;
    }
    return valB - valA;
  });
}

export function searchIndexes(indexes, query) {
  if (!query) return indexes;
  const q = query.toLowerCase();
  return indexes.filter(
    (idx) =>
      idx.index_name.toLowerCase().includes(q) ||
      idx.index_code.toLowerCase().includes(q),
  );
}

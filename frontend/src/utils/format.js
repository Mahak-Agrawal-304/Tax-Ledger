const inrFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

const inrFormatterPrecise = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 2,
});

export function formatINR(value, { precise = false } = {}) {
  const amount = Number.isFinite(value) ? value : 0;
  return (precise ? inrFormatterPrecise : inrFormatter).format(amount);
}

export function parseINRInput(raw) {
  const cleaned = String(raw).replace(/[^0-9.]/g, "");
  const value = parseFloat(cleaned);
  return Number.isNaN(value) ? 0 : value;
}

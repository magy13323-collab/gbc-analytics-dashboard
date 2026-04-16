function validateEnv() {
  if (!process.env.SUPABASE_URL) {
    throw new Error("SUPABASE_URL is not set");
  }
  if (!process.env.SUPABASE_KEY) {
    throw new Error("SUPABASE_KEY is not set");
  }
}

function toDateKey(value) {
  if (!value) {
    return null;
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }

  return parsed.toISOString().slice(0, 16);
}

async function getOrdersByDay() {
  validateEnv();

  const endpoint = new URL("/rest/v1/orders", process.env.SUPABASE_URL);
  endpoint.searchParams.set("select", "created_at");
  endpoint.searchParams.set("order", "created_at.asc");
  endpoint.searchParams.set("limit", "10000");

  const response = await fetch(endpoint, {
    headers: {
      apikey: process.env.SUPABASE_KEY,
      Authorization: `Bearer ${process.env.SUPABASE_KEY}`,
    },
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Supabase error: ${response.status} ${text}`);
  }

  const rows = await response.json();
  const countsByMinute = new Map();

  for (const row of rows) {
    const minuteKey = toDateKey(row.created_at);
    if (!minuteKey) {
      continue;
    }

    countsByMinute.set(minuteKey, (countsByMinute.get(minuteKey) || 0) + 1);
  }

  const points = [...countsByMinute.entries()]
    .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))
    .map(([date, count]) => ({ date, count }));

  return {
    totalOrders: rows.length,
    points,
  };
}

module.exports = {
  getOrdersByDay,
};

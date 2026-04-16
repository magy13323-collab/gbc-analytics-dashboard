const fs = require("fs");
const http = require("http");
const path = require("path");
const { getOrdersByDay } = require("./lib/orders-by-day");

function loadDotEnv() {
  const envPath = path.join(__dirname, ".env");
  if (!fs.existsSync(envPath)) {
    return;
  }

  const lines = fs.readFileSync(envPath, "utf8").split(/\r?\n/);
  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#") || !line.includes("=")) {
      continue;
    }

    const [key, ...rest] = line.split("=");
    const value = rest.join("=");
    if (!process.env[key]) {
      process.env[key] = value;
    }
  }
}

function sendJson(res, statusCode, payload) {
  res.writeHead(statusCode, { "Content-Type": "application/json; charset=utf-8" });
  res.end(JSON.stringify(payload));
}

loadDotEnv();

const server = http.createServer(async (req, res) => {
  if (!req.url) {
    return sendJson(res, 400, { error: "Bad request" });
  }

  if (req.url === "/api/orders-by-day" && req.method === "GET") {
    try {
      const data = await getOrdersByDay();
      return sendJson(res, 200, data);
    } catch (error) {
      return sendJson(res, 500, {
        error: "Failed to load orders",
        details: error.message,
      });
    }
  }

  if ((req.url === "/" || req.url === "/index.html") && req.method === "GET") {
    const filePath = path.join(__dirname, "index.html");
    const html = fs.readFileSync(filePath, "utf8");
    res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
    res.end(html);
    return;
  }

  sendJson(res, 404, { error: "Not found" });
});

const port = Number(process.env.PORT || 3000);
server.listen(port, () => {
  console.log(`Dashboard is running on http://localhost:${port}`);
});

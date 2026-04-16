const { getOrdersByDay } = require("../lib/orders-by-day");

module.exports = async (req, res) => {
  if (req.method !== "GET") {
    res.setHeader("Allow", "GET");
    return res.status(405).json({ error: "Method Not Allowed" });
  }

  try {
    const data = await getOrdersByDay();
    return res.status(200).json(data);
  } catch (error) {
    return res.status(500).json({
      error: "Failed to load orders",
      details: error.message,
    });
  }
};

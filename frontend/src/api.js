
const API_BASE_URL = "https://opspilot-api-opbm.onrender.com";

export async function investigateService(service = "payment-api") {
  const response = await fetch(`${API_BASE_URL}/api/investigate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ service }),
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(`Investigation failed (${response.status}): ${message}`);
  }

  return response.json();
}

export async function getServiceMetrics(service = "payment-api") {
  const response = await fetch(
    `${API_BASE_URL}/api/metrics/${encodeURIComponent(service)}`
  );

  if (!response.ok) {
    const message = await response.text();
    throw new Error(`Metrics request failed (${response.status}): ${message}`);
  }

  return response.json();
}

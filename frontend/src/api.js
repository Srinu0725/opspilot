
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8002";

/**
 * Investigate an incident using an uploaded report.
 *
 * incidentReport can be:
 * - A File object selected from an <input type="file">
 * - An object containing { file: File }
 * - An object containing { fileName, markdown } (legacy format)
 */
export async function investigateService(
  service = "payment-api",
  incidentReport = null
) {
  if (!incidentReport) {
    throw new Error("Please select an incident report file.");
  }

  // Support either a File object or an object wrapping the File.
  const file =
    incidentReport instanceof File
      ? incidentReport
      : incidentReport.file instanceof File
        ? incidentReport.file
        : null;

  if (!file) {
    throw new Error(
      "investigateService requires a File object. Pass the selected file, not just its filename or extracted text."
    );
  }

  const formData = new FormData();
  formData.append("service", service.trim());
  formData.append("file", file);

  const response = await fetch(
    `${API_BASE_URL}/incidents/investigate`,
    {
      method: "POST",
      body: formData,
    }
  );

  if (!response.ok) {
    const message = await response.text();
    throw new Error(
      `Investigation failed (${response.status}): ${message}`
    );
  }

  return response.json();
}

export async function getServiceMetrics(service = "payment-api") {
  const response = await fetch(
    `${API_BASE_URL}/api/metrics/${encodeURIComponent(service)}`
  );

  if (!response.ok) {
    const message = await response.text();
    throw new Error(
      `Metrics request failed (${response.status}): ${message}`
    );
  }

  return response.json();
}

export async function callMcpTool(tool, arguments_ = {}) {
  const response = await fetch(`${API_BASE_URL}/api/mcp/call`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      tool,
      arguments: arguments_,
    }),
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(
      `MCP tool call failed (${response.status}): ${message}`
    );
  }

  const result = await response.json();

  if (result.is_error) {
    const message = (result.content || [])
      .map((item) => item.text || "")
      .join("\n");

    throw new Error(message || "MCP tool execution failed.");
  }

  return result;
}

export async function chatWithOpsPilot(
  question,
  history = [],
  context = {}
) {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question,
      history,
      context,
    }),
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(`Chat failed (${response.status}): ${message}`);
  }

  return response.json();
}

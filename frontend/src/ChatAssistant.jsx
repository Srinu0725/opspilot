
import { useState } from "react";
import { callMcpTool, chatWithOpsPilot } from "./api";
import "./ChatAssistant.css";

const suggestions = [
  {
    title: "Investigate an incident",
    prompt: "Investigate why the payment API is slow",
    icon: "⌕",
  },
  {
    title: "Inspect service metrics",
    prompt: "Show the latest payment API metrics",
    icon: "↗",
  },
  {
    title: "Search runbooks",
    prompt: "Find runbook guidance for database latency",
    icon: "≡",
  },
];

function parseToolResponse(response) {
  if (response?.structured_content) {
    const data = response.structured_content;
    return data.result ?? data;
  }

  const items = (response?.content ?? [])
    .filter((item) => item.type === "text" && item.text)
    .map((item) => {
      try {
        return JSON.parse(item.text);
      } catch {
        return item.text;
      }
    });

  if (items.length === 1) return items[0];
  return items;
}

function compactContext(result) {
  if (!result) return {};

  const data = result.data;
  if (result.tool !== "investigate_service") {
    return { last_tool: result.tool, result: data };
  }

  const summary = data?.investigation_summary ?? {};
  const rca = data?.rca_analysis ?? {};

  return {
    service: data?.service,
    hypothesis: rca.hypotheses?.[0] ?? null,
    anomalies: summary.observed_anomalies ?? [],
    key_logs: summary.key_logs ?? [],
    deployment: summary.deployment_correlation ?? data?.deployment ?? null,
    missing_evidence: rca.missing_evidence ?? summary.missing_evidence ?? [],
    runbook_guidance: rca.runbook_guidance ?? [],
  };
}

function InvestigationCard({ result }) {
  const data = result.data;

  if (result.tool !== "investigate_service") {
    return (
      <details className="op-raw-result">
        <summary>View tool results</summary>
        <pre>{JSON.stringify(data, null, 2)}</pre>
      </details>
    );
  }

  const summary = data?.investigation_summary ?? {};
  const rca = data?.rca_analysis ?? {};
  const hypothesis = rca.hypotheses?.[0];
  const confidence = hypothesis?.confidence;
  const anomalies = summary.observed_anomalies ?? [];
  const support = hypothesis?.support ?? [];
  const missing =
    rca.missing_evidence ??
    summary.missing_evidence ??
    confidence?.limitations ??
    [];
  const timeline = data?.timeline ?? [];
  const logs = data?.logs ?? [];
  const deployment = data?.deployment;
  const runbooks = data?.runbook_context ?? [];

  const events = [
    ...timeline.map((event, index) => ({
      id: `timeline-${index}`,
      time: event.timestamp,
      title: event.description ?? event.observation ?? event.event_type ?? "Investigation event",
      source: event.source,
    })),
    ...logs.slice(0, 5).map((log, index) => ({
      id: `log-${index}`,
      time: log.timestamp,
      title: log.message ?? log.content ?? log.observation ?? "Log evidence",
      source: log.source,
    })),
  ].sort((a, b) => {
    if (!a.time) return 1;
    if (!b.time) return -1;
    return new Date(a.time) - new Date(b.time);
  });

  const guidance = runbooks.flatMap((context) =>
    Array.isArray(context?.results) ? context.results : [context]
  );

  const confidenceScore =
    typeof confidence === "number" ? confidence : confidence?.score;

  return (
    <div className="op-investigation">
      <div className="op-result-heading">
        <span className="op-status-dot" />
        <span>Investigation complete</span>
        <span className="op-confidence">
          {confidence?.level ?? "Unrated"} confidence
          {typeof confidenceScore === "number" &&
            ` · ${Math.round(
              confidenceScore <= 1
                ? confidenceScore * 100
                : confidenceScore
            )}%`}
        </span>
      </div>

      <section className="op-cause">
        <div className="op-section-label">LIKELY ROOT CAUSE</div>
        <h3>
          {hypothesis?.hypothesis ??
            "No root-cause hypothesis was returned."}
        </h3>
        <p>
          This is a hypothesis based on available evidence, not a confirmed
          root cause.
        </p>
      </section>

      <section className="op-result-section">
        <div className="op-section-title">
          <span>Supporting evidence</span>
        </div>
        {support.length > 0 ? (
          <ul>
            {support.map((item, index) => (
              <li key={index}>
                {typeof item === "string"
                  ? item
                  : item.description ?? item.observation ?? JSON.stringify(item)}
              </li>
            ))}
          </ul>
        ) : (
          <p className="op-muted">No supporting evidence was returned.</p>
        )}
      </section>

      <section className="op-result-section">
        <div className="op-section-title">
          <span>Detected anomalies</span>
          <span className="op-count">{anomalies.length}</span>
        </div>
        {anomalies.length > 0 ? (
          <div className="op-anomaly-grid">
            {anomalies.map((item, index) => (
              <div className="op-anomaly" key={`${item.metric}-${index}`}>
                <span>{item.metric?.replaceAll("_", " ")}</span>
                <strong>
                  {item.current}
                  {item.metric?.includes("percent") ? "%" : ""}
                </strong>
                <small>
                  Baseline: {item.baseline}
                  {item.change_percent != null &&
                    ` · Change: ${item.change_percent}%`}
                </small>
              </div>
            ))}
          </div>
        ) : (
          <p className="op-muted">
            See the evidence and root-cause analysis for metric findings.
          </p>
        )}
      </section>

      {deployment && (
        <section className="op-result-section">
          <div className="op-section-title">Deployment correlation</div>
          <pre>{JSON.stringify(deployment, null, 2)}</pre>
        </section>
      )}

      <section className="op-result-section">
        <div className="op-section-title">
          <span>Investigation timeline</span>
          <span className="op-count">{events.length}</span>
        </div>
        {events.length > 0 ? (
          <ol className="op-recommendations">
            {events.map((event) => (
              <li key={event.id}>
                <span className="op-step-number">
                  {event.time
                    ? new Date(event.time).toLocaleTimeString()
                    : "Event"}
                </span>
                <span>
                  {event.title}
                  {event.source && <small> · {event.source}</small>}
                </span>
              </li>
            ))}
          </ol>
        ) : (
          <p className="op-muted">
            No timestamped timeline events were returned.
          </p>
        )}
      </section>

      {missing.length > 0 && (
        <section className="op-missing">
          <strong>Evidence still needed</strong>
          <ul>
            {missing.map((item, index) => (
              <li key={index}>
                {typeof item === "string"
                  ? item
                  : item.description ?? item.observation ?? JSON.stringify(item)}
              </li>
            ))}
          </ul>
        </section>
      )}

      {guidance.length > 0 && (
        <details className="op-raw-result">
          <summary>View retrieved runbook context</summary>
          {guidance.slice(0, 5).map((item, index) => (
            <div key={index}>
              <strong>
                {item.document?.section ?? item.section ?? "Runbook evidence"}
              </strong>
              <p>
                {item.document?.content ?? item.content ?? item.text ?? ""}
              </p>
            </div>
          ))}
        </details>
      )}

      <details className="op-raw-result">
        <summary>Inspect raw investigation data</summary>
        <pre>{JSON.stringify(data, null, 2)}</pre>
      </details>
    </div>
  );
}

export default function ChatAssistant() {
  const [service, setService] = useState("payment-api");
  const [prompt, setPrompt] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Hello, I'm OpsPilot. I can investigate incidents, examine service metrics, and search your runbooks. What would you like me to look into?",
    },
  ]);

  const lastInvestigation = [...messages]
  .reverse()
  .find(
    (message) =>
      message.role === "assistant" &&
      message.result?.tool === "investigate_service" &&
      message.result?.data
  )?.result?.data;

  async function sendMessage(value = prompt) {
    const question = value.trim();
    if (!question || busy) return;

    const previousMessages = messages;
    const history = previousMessages.slice(-10).map(({ role, text }) => ({
      role,
      text,
    }));

    setMessages((previous) => [
      ...previous,
      { role: "user", text: question },
    ]);
    setPrompt("");
    setError("");
    setBusy(true);

    const lower = question.toLowerCase();
    const followUp =
      /^(why|how|what does|explain|could|should|which|tell me more|what about|is it|can you explain)/i.test(
        question
      );

    let tool = null;
    let args = { service };

    if (
      !followUp &&
      (lower.includes("runbook") ||
        lower.includes("guidance") ||
        lower.includes("troubleshooting"))
    ) {
      tool = "find_runbook_guidance";
      args = { service, query: question, top_k: 3 };
    } else if (
      !followUp &&
      (lower.includes("metrics") ||
        lower.includes("p95") ||
        lower.includes("p99") ||
        lower.includes("cpu") ||
        lower.includes("error rate"))
    ) {
      tool = "get_metrics";
    } else if (
      !followUp &&
      (lower.includes("investigate") ||
        lower.includes("incident") ||
        lower.includes("root cause") ||
        lower.includes("latency") ||
        lower.includes("slow"))
    ) {
      tool = "investigate_service";
    }

    try {
      if (tool) {
        const response = await callMcpTool(tool, args);

        if (response.is_error) {
          throw new Error(
            response.content?.map((item) => item.text).join("\n") ||
              "The MCP tool reported an error."
          );
        }

        const data = parseToolResponse(response);
        const result = { tool, data };

        setMessages((previous) => [
          ...previous,
          {
            role: "assistant",
            text: `I've completed ${tool.replaceAll("_", " ")} for ${service}. Here's what I found.`,
            result,
          },
        ]);
      } else {
        const context = lastInvestigation
  ? {
      service: lastInvestigation.service,
      hypothesis:
        lastInvestigation.rca_analysis?.hypotheses?.[0] ?? null,
      anomalies:
        lastInvestigation.investigation_summary?.observed_anomalies ?? [],
      key_logs: lastInvestigation.logs ?? [],
      deployment: lastInvestigation.deployment ?? null,
      missing_evidence:
        lastInvestigation.rca_analysis?.hypotheses?.[0]?.confidence
          ?.limitations ?? [],
      runbook_guidance:
        lastInvestigation.rca_analysis?.runbook_guidance ?? [],
    }
  : {};

        const response = await chatWithOpsPilot(question, history, {
        service,
        previous_investigation: context ?? null,
        evidence_source: "MCP investigation results; verify whether telemetry is simulated or live.",
        });

        setMessages((previous) => [
          ...previous,
          {
            role: "assistant",
            text: response.answer,
          },
        ]);
      }
    } catch (err) {
      setError(err.message || "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="op-page">
      <div className="op-shell">
        <header className="op-header">
          <div className="op-brand">
            <div className="op-brand-mark">O</div>
            <div>
              <h1>OpsPilot</h1>
              <p>AI incident response assistant</p>
            </div>
          </div>
          <div className="op-header-right">
            <span className="op-online">
              <span className="op-status-dot" /> MCP connected
            </span>
            <label className="op-service">
              <span>Service</span>
              <input
                value={service}
                onChange={(event) => setService(event.target.value)}
                aria-label="Service name"
                disabled={busy}
              />
            </label>
          </div>
        </header>

        <section className="op-workspace">
          <div className="op-welcome">
            <div className="op-eyebrow">INCIDENT INTELLIGENCE</div>
            <h2>What can I help you investigate?</h2>
            <p>
              Ask a question, inspect observability data, or get troubleshooting
              guidance from your runbooks.
            </p>
          </div>

          <div className="op-suggestions">
            {suggestions.map((item) => (
              <button
                className="op-suggestion"
                key={item.title}
                onClick={() => sendMessage(item.prompt)}
                disabled={busy}
                type="button"
              >
                <span className="op-suggestion-icon">{item.icon}</span>
                <span className="op-suggestion-copy">
                  <strong>{item.title}</strong>
                  <small>{item.prompt}</small>
                </span>
                <span className="op-suggestion-arrow">↗</span>
              </button>
            ))}
          </div>

          <div className="op-chat-label">
            <span>CONVERSATION</span>
            <button
              type="button"
              onClick={() =>
                setMessages([
                  {
                    role: "assistant",
                    text: "Conversation cleared. What would you like to investigate?",
                  },
                ])
              }
              disabled={busy}
            >
              Clear chat
            </button>
          </div>

          <section className="op-messages" aria-live="polite">
            {messages.map((message, index) => (
              <article
                key={index}
                className={`op-message op-message-${message.role}`}
              >
                <div className="op-avatar">
                  {message.role === "user" ? "Y" : "O"}
                </div>
                <div className="op-message-body">
                  <div className="op-message-meta">
                    <strong>
                      {message.role === "user" ? "You" : "OpsPilot"}
                    </strong>
                    {message.result && <span>Tool result</span>}
                  </div>
                  <p className="op-message-text">{message.text}</p>
                  {message.result && (
                    <InvestigationCard result={message.result} />
                  )}
                </div>
              </article>
            ))}

            {busy && (
              <div className="op-typing">
                <span className="op-typing-dots">
                  <i />
                  <i />
                  <i />
                </span>
                <span>OpsPilot is working on your request…</span>
              </div>
            )}

            {error && (
              <div className="op-error" role="alert">
                <strong>Request failed</strong>
                <p>{error}</p>
                <button type="button" onClick={() => setError("")}>
                  Dismiss
                </button>
              </div>
            )}
          </section>

          <form
            className="op-composer"
            onSubmit={(event) => {
              event.preventDefault();
              sendMessage();
            }}
          >
            <input
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              placeholder="Ask a follow-up or investigate another issue…"
              aria-label="Message OpsPilot"
              disabled={busy}
            />
            <button type="submit" disabled={busy || !prompt.trim()}>
              <span>{busy ? "Working…" : "Send"}</span>
              <span aria-hidden="true">↑</span>
            </button>
          </form>
          <p className="op-footnote">
            OpsPilot uses MCP tools and available evidence. Root-cause
            conclusions should be verified before taking production action.
          </p>
        </section>
      </div>
    </main>
  );
}

import { useState } from "react";
import "./App.css";
import { investigateService } from "./api";

function formatTime(timestamp) {
  if (!timestamp) return "Time unavailable";
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return timestamp;
  return date.toISOString().slice(11, 19) + " UTC";
}

function getHypotheses(result) {
  return (
    result?.rca_analysis?.hypotheses ??
    result?.final_report?.root_cause_hypotheses ??
    result?.root_cause_hypotheses ??
    []
  );
}

function getConfidence(hypothesis) {
  const confidence = hypothesis?.confidence;
  const score =
    typeof confidence === "number" ? confidence : confidence?.score;

  if (typeof score !== "number") return null;
  return score <= 1 ? score * 100 : score;
}

function getEvidence(result) {
  const timeline = result?.timeline ?? result?.investigation_summary?.timeline;

  if (Array.isArray(timeline) && timeline.length) {
    return timeline.map((event, index) => ({
      id: `${event.timestamp ?? "event"}-${index}`,
      time: event.timestamp,
      type: event.event_type ?? event.type ?? "event",
      title: event.description ?? event.observation ?? "Investigation event",
      source: event.source,
    }));
  }

  return (result?.evidence ?? []).map((event, index) => ({
    id: `${event.timestamp ?? "event"}-${index}`,
    time: event.timestamp,
    type: event.evidence_type ?? "evidence",
    title: event.observation ?? "Evidence recorded",
    source: event.source,
  }));
}

function getMissingEvidence(result, hypothesis) {
  return (
    result?.rca_analysis?.missing_evidence ??
    result?.final_report?.missing_evidence ??
    result?.missing_evidence ??
    hypothesis?.confidence?.limitations ??
    []
  );
}

function getRecommendations(result) {
  return (
    result?.rca_analysis?.recommendations ??
    result?.final_report?.recommended_next_steps ??
    result?.recommended_next_steps ??
    []
  );
}

function getRunbookItems(result) {
  const contexts = result?.runbook_context ?? result?.runbook_guidance ?? [];

  return contexts.flatMap((context) =>
    Array.isArray(context?.results) ? context.results : [context]
  );
}


function findMetric(result, ...names) {
  const metricMap = result?.metric_analysis?.metrics ?? {};

  for (const name of names) {
    const metric = metricMap[name];

    if (metric && typeof metric === "object") {
      return metric;
    }
  }

  return null;
}


// function findMetric(result, ...names) {
//   const metricAnalysis = result?.metric_analysis?.metrics ?? {};
//   const metrics = result?.metrics?.metrics ?? [];

//   // Prefer metric-analysis values, which may contain current and baseline.
//   for (const name of names) {
//     const entry = Object.entries(metricAnalysis).find(
//       ([key]) => key.toLowerCase() === name.toLowerCase()
//     );

//     if (entry) {
//       const value = entry[1];

//       if (value && typeof value === "object") {
//         return (
//           value.current ??
//           value.current_value ??
//           value.value ??
//           value.latest ??
//           null
//         );
//       }

//       return value;
//     }
//   }

//   // Fall back to partial name matches in the metrics payload.
//   const entry = metrics.find((item) => {
//     const key = String(item.name ?? item.metric ?? item.key ?? "").toLowerCase();
//     return names.some((name) => key.includes(name.toLowerCase()));
//   });

//   if (!entry) return null;

//   return entry.value ?? entry.current ?? entry.current_value ?? null;
// }


function displayMetric(metric, suffix = "") {
  if (metric == null) return "—";

  const value =
    typeof metric === "object"
      ? metric.current
      : metric;

  if (value == null || !Number.isFinite(Number(value))) {
    return "—";
  }

  return `${Number(value).toLocaleString()}${suffix}`;
}


function App() {
  const [service, setService] = useState("payment-api");
  const [investigating, setInvestigating] = useState(false);
  const [notice, setNotice] = useState("");
  const [result, setResult] = useState(null);

  async function runInvestigation() {
    setInvestigating(true);
    setNotice("");

    try {
      const data = await investigateService(service);
      setResult(data);
      console.log(
        "Metric details:",
        JSON.stringify(
          {
            p95: data.metric_analysis?.metrics?.p95_ms,
            p99: data.metric_analysis?.metrics?.p99_ms,
            databaseLatency:
              data.metric_analysis?.metrics?.database_latency_ms,
            cpu: data.metric_analysis?.metrics?.cpu_percent,
            memory: data.metric_analysis?.metrics?.memory_percent,
            allMetrics: data.metric_analysis?.metrics,
          },
          null,
          2
        )
      );
      setNotice("Investigation completed successfully.");
      console.log("Investigation result:", data);
    } catch (error) {
      setNotice(`Investigation failed: ${error.message}`);
    } finally {
      setInvestigating(false);
    }
  }

  const hypotheses = getHypotheses(result);
  const primaryHypothesis = hypotheses[0];
  const confidence = getConfidence(primaryHypothesis);
  const evidence = getEvidence(result);
  const missingEvidence = getMissingEvidence(result, primaryHypothesis);
  const recommendations = getRecommendations(result);
  const runbookItems = getRunbookItems(result);

  const apiLatency = findMetric(result, "p95_ms");
  const dbLatency = findMetric(result, "database_latency_ms");
  const cpu = findMetric(result, "cpu_percent");
  const memory = findMetric(result, "memory_percent");

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">O</div>
          <div>
            <h1>OpsPilot</h1>
            <span>INCIDENT INTELLIGENCE</span>
          </div>
        </div>

        <div className="nav-label">WORKSPACE</div>
        <button className="nav-item active"><span>▦</span> Overview</button>
        <button
          className="nav-item"
          onClick={() => setNotice("Incident history is not implemented yet.")}
        >
          <span>◷</span> Incident history
        </button>
        <button
          className="nav-item"
          onClick={() => setNotice("Service management is not implemented yet.")}
        >
          <span>⌘</span> Services
        </button>

        <div className="sidebar-bottom">
          <div className="connection-indicator" />
          <div>
            <strong>MCP service</strong>
            <p>Connected through API bridge</p>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <p className="eyebrow">OPERATIONS / OVERVIEW</p>
            <h2>Incident command center</h2>
          </div>
          <div className="topbar-right">
            <span className="demo-badge">
              {result ? "INVESTIGATION RESULTS" : "AWAITING INVESTIGATION"}
            </span>
            <div className="avatar">OP</div>
          </div>
        </header>

        <section className="welcome-row">
          <div>
            <h3>Production health overview</h3>
            <p>Correlate metrics, logs, deployments, and runbooks to investigate incidents.</p>
          </div>
          <div className="service-picker">
            <label htmlFor="service">SERVICE</label>
            <select
              id="service"
              value={service}
              onChange={(event) => setService(event.target.value)}
            >
              <option value="payment-api">payment-api</option>
            </select>
          </div>
        </section>

        
        {/* <section className="stats-grid">
          <article className="stat-card">
            <div className="stat-heading">API P95 LATENCY</div>
            <div className="stat-value">
              {displayMetric(findMetric(result, "p95_ms"))}
              {findMetric(result, "p95_ms")?.current != null && (
                <small> ms</small>
              )}
            </div>
            <div className="stat-foot">From investigation metrics</div>
          </article>

          <article className="stat-card">
            <div className="stat-heading">DATABASE LATENCY</div>
            <div className="stat-value">
              {displayMetric(findMetric(result, "database_latency_ms"))}
              {findMetric(result, "database_latency_ms")?.current != null && (
                <small> ms</small>
              )}
            </div>
            <div className="stat-foot">From investigation metrics</div>
          </article>

          <article className="stat-card">
            <div className="stat-heading">CPU UTILIZATION</div>
            <div className="stat-value">
              {displayMetric(findMetric(result, "cpu_percent"))}
              {findMetric(result, "cpu_percent")?.current != null && (
                <small>%</small>
              )}
            </div>
            <div className="stat-foot">From investigation metrics</div>
          </article>

          <article className="stat-card">
            <div className="stat-heading">MEMORY UTILIZATION</div>
            <div className="stat-value">
              {displayMetric(findMetric(result, "memory_percent"))}
              {findMetric(result, "memory_percent")?.current != null && (
                <small>%</small>
              )}
            </div>
            <div className="stat-foot">From investigation metrics</div>
          </article>
        </section> */}

        
        {result && (
          <section className="incident-summary">
            <div className="incident-summary-main">
              <span className="incident-summary-label">
                INCIDENT STATUS
              </span>
              <h3>Service degradation detected</h3>
              <p>
                {result.final_report?.incident ??
                  "Anomalies detected in service metrics. Review the correlated evidence."}
              </p>
            </div>

            <div className="incident-summary-count">
              <strong>
                {
                  Object.values(result.metric_analysis?.metrics ?? {})
                    .filter((metric) => metric?.anomaly).length
                }
              </strong>
              <span>Anomalous metrics</span>
            </div>
          </section>
        )}

        
        
        
        <section className="stats-grid">
          {[
            { title: "API P95 LATENCY", key: "p95_ms", unit: "ms" },
            {
              title: "DATABASE LATENCY",
              key: "database_latency_ms",
              unit: "ms",
            },
            { title: "CPU UTILIZATION", key: "cpu_percent", unit: "%" },
            { title: "MEMORY UTILIZATION", key: "memory_percent", unit: "%" },
            {
              title: "ERROR RATE",
              key: "error_rate_percent",
              unit: "%",
            },

          ].map(({ title, key, unit }) => {
            const metric = findMetric(result, key);

            const formatValue = (value) =>
              value == null ? "—" : Number(value).toLocaleString("en-US", {
                maximumFractionDigits: 2,
              });

            return (
              <article
                  className={`stat-card ${
                    metric?.anomaly ? "stat-card-anomaly" : "stat-card-normal"
                  }`}
                  key={key}
                  >
                <div className="stat-heading">{title}</div>

                <div className="stat-value">
                  {displayMetric(metric)}
                  {metric?.current != null && (
                    <small>{unit}</small>
                  )}
                </div>

                <div className="stat-foot">
                  Baseline: {formatValue(metric?.baseline)} {unit}
                </div>

                <div className="stat-foot">
                  Change:{" "}
                  {metric?.change_percent == null
                    ? "—"
                    : `${metric.change_percent > 0 ? "+" : ""}${formatValue(
                        metric.change_percent
                      )}%`}
                </div>
              </article>
            );
          })}
        </section>




        <section className="incident-banner">
          <div className="incident-symbol">!</div>
          <div className="incident-copy">
            <span className="incident-label">
              {result ? "INVESTIGATION COMPLETE" : "INCIDENT INVESTIGATION"}
            </span>
            <h3>
              {result?.final_report?.incident ??
                "Investigate elevated service latency"}
            </h3>
            <p>
              {result
                ? `Service: ${result.affected_service ?? result.service ?? service}`
                : "Run an investigation to retrieve results from the OpsPilot backend."}
            </p>
          </div>
          <button
            className="primary-button"
            onClick={runInvestigation}
            disabled={investigating}
          >
            {investigating ? "Investigating..." : "Run investigation →"}
          </button>
        </section>

        {notice && (
          <div className="notice" role="status">
            {notice}
            <button onClick={() => setNotice("")}>Dismiss</button>
          </div>
        )}

        <div className="content-grid">
          <section className="panel hypothesis-panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">AI ANALYSIS</p>
                <h3>Root cause hypothesis</h3>
              </div>
              {confidence !== null && (
                <span className="confidence-badge">
                  {Math.round(confidence)}% confidence
                </span>
              )}
            </div>

            {primaryHypothesis ? (
              <>
                <h4>
                  {primaryHypothesis.hypothesis ??
                    primaryHypothesis.title ??
                    "Root cause hypothesis"}
                </h4>
                <p className="panel-description">
                  {primaryHypothesis.explanation ??
                    primaryHypothesis.rationale ??
                    "Based on correlated investigation evidence."}
                </p>

                {confidence !== null && (
                  <div className="confidence-track">
                    <div style={{ width: `${Math.max(0, Math.min(100, confidence))}%` }} />
                  </div>
                )}

                <div className="section-label">SUPPORTING EVIDENCE</div>
                <ul className="evidence-list">
                  {(
                    primaryHypothesis.support ??
                    primaryHypothesis.supporting_evidence ??
                    result?.rca_analysis?.strong_evidence ??
                    []
                  ).slice(0, 6).map((item, index) => (
                    <li key={index}>
                      <span className="check">✓</span>
                      {typeof item === "string"
                        ? item
                        : item.description ?? item.observation ?? JSON.stringify(item)}
                    </li>
                  ))}
                </ul>
              </>
            ) : (
              <p className="panel-description">
                Run an investigation to display its root-cause hypothesis.
              </p>
            )}

            <div className="limitation-box">
              <strong>Evidence still needed</strong>
              {missingEvidence.length > 0 ? (
                <ul>
                  {missingEvidence.slice(0, 5).map((item, index) => (
                    <li key={index}>
                      {typeof item === "string"
                        ? item
                        : item.description ?? item.observation ?? JSON.stringify(item)}
                    </li>
                  ))}
                </ul>
              ) : (
                <p>{result ? "No missing evidence was reported." : "Run an investigation to see missing evidence."}</p>
              )}
            </div>
          </section>

          <section className="panel timeline-panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">CORRELATED SIGNALS</p>
                <h3>Evidence timeline</h3>
              </div>
              <span className="muted-label">{evidence.length} events</span>
            </div>

            {evidence.length ? (
              <div className="timeline">
                {evidence.slice(0, 12).map((event) => (
                  <article className="timeline-item" key={event.id}>
                    <div className={`timeline-dot ${
                      /error|critical|timeout/i.test(event.title)
                        ? "critical"
                        : /warn|latency/i.test(event.title)
                          ? "warning"
                          : "info"
                    }`} />
                    <div className="timeline-content">
                      <div className="timeline-meta">
                        <span>{String(event.type).toUpperCase()}</span>
                        <time>{formatTime(event.time)}</time>
                      </div>
                      <h4>{event.title}</h4>
                      {event.source && <p>Source: {event.source}</p>}
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <p className="panel-description">Investigation events will appear here.</p>
            )}
          </section>

          <section className="panel runbook-panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">RECOMMENDED ACTIONS</p>
                <h3>Runbook guidance</h3>
              </div>
              <span className="runbook-tag">Retrieved context</span>
            </div>

            <p className="panel-description">
              Recommendations are advisory. Validate the evidence before making production changes.
            </p>

            {recommendations.length ? (
              <ol className="runbook-list">
                {recommendations.slice(0, 8).map((item, index) => (
                  <li key={index}>
                    <span>{String(index + 1).padStart(2, "0")}</span>
                    {typeof item === "string"
                      ? item
                      : item.description ?? item.recommendation ?? JSON.stringify(item)}
                  </li>
                ))}
              </ol>
            ) : runbookItems.length ? (
              <ol className="runbook-list">
                {runbookItems.slice(0, 8).map((item, index) => (
                  <li key={index}>
                    <span>{String(index + 1).padStart(2, "0")}</span>
                    <div>
                      <strong>{item.section ?? item.title ?? "Runbook guidance"}</strong>
                      <p>{item.content ?? item.text ?? item.query ?? ""}</p>
                    </div>
                  </li>
                ))}
              </ol>
            ) : (
              <p className="panel-description">Runbook guidance will appear after an investigation.</p>
            )}

            <div className="read-only-note">
              <span>READ-ONLY MODE</span>
              <p>OpsPilot recommends actions but does not execute production changes.</p>
            </div>
          </section>
        </div>

        <footer className="footer">
          <span>OpsPilot · Incident investigation workspace</span>
          <span>{result ? "Investigation data received from backend" : "No investigation loaded"}</span>
        </footer>
      </main>
    </div>
  );
}

export default App;

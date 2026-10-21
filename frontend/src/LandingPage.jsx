
import { useRef, useState } from "react";
import "./LandingPage.css";

function detectService(text) {
  const patterns = [
    /^\s*(?:[-*]\s*)?(?:affected service|service)\s*:\s*`?([a-zA-Z0-9._-]+)`?/im,
    /^\s*#{1,4}\s*(?:affected service|service)\s*\n+\s*`?([a-zA-Z0-9._-]+)`?/im,
  ];

  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match?.[1]) return match[1];
  }

  return "";
}

export default function LandingPage({ onStartInvestigation }) {
  const picker = useRef(null);

  const [selectedFile, setSelectedFile] = useState(null);
  const [fileName, setFileName] = useState("");
  const [markdown, setMarkdown] = useState("");
  const [service, setService] = useState("");
  const [error, setError] = useState("");
  const [dragging, setDragging] = useState(false);

  async function loadFile(file) {
    setError("");

    if (!file) return;

    const extension = file.name.split(".").pop()?.toLowerCase();
    const supportedExtensions = ["md", "txt", "csv", "log"];

    if (!supportedExtensions.includes(extension)) {
      setError("Choose a .txt, .md, .csv, or .log incident report.");
      return;
    }

    if (file.size > 1024 * 1024) {
      setError("The file must be 1 MB or smaller.");
      return;
    }

    try {
      const text = await file.text();

      if (!text.trim()) {
        setError("The selected file is empty.");
        return;
      }

      // Keep the actual File object for the multipart upload.
      setSelectedFile(file);
      setFileName(file.name);
      setMarkdown(text);

      const detectedService = detectService(text);
      setService(detectedService || "payment-api");
    } catch {
      setError("Could not read the file. Please try again.");
    }
  }

  function removeFile() {
    setSelectedFile(null);
    setFileName("");
    setMarkdown("");
    setService("");
    setError("");
  }

  function startInvestigation() {
    if (!selectedFile) {
      setError("Upload an incident report first.");
      return;
    }

    if (!service.trim()) {
      setError("Enter the affected service name.");
      return;
    }

    const incident = {
      file: selectedFile,
      fileName,
      markdown,
      service: service.trim(),
    };

    console.log("Submitting incident:", {
      fileName: selectedFile.name,
      fileSize: selectedFile.size,
      reportLength: markdown.length,
      service: service.trim(),
      actualFileAttached: incident.file instanceof File,
    });

    onStartInvestigation?.(incident);
  }

  return (
    <main className="ops-landing">
      <header className="ops-topbar">
        <a className="ops-brand" href="#top">
          <span className="ops-brand-mark">O</span>
          OpsPilot
        </a>
        <span className="ops-topbar-label">INCIDENT INTELLIGENCE</span>
      </header>

      <section className="ops-hero" id="top">
        <div className="ops-hero-copy">
          <div className="ops-eyebrow">
            <span className="ops-status-dot" />
            PRODUCTION INCIDENT RESPONSE
          </div>

          <h1>
            Turn production incidents into <em>clear next steps.</em>
          </h1>

          <p className="ops-hero-description">
            Bring an incident report. Organize investigation around service
            evidence, metrics, and runbook guidance.
          </p>

          <div className="ops-trust-row">
            <span>Read-only investigation workflow</span>
            <span>Evidence-first findings</span>
          </div>
        </div>

        <section className="ops-intake-card">
          <div className="ops-step-label">START HERE / 01</div>
          <h2>Submit an incident</h2>
          <p className="ops-muted">
            Upload a supported incident report and review it before proceeding.
          </p>

          <button
            type="button"
            className={`ops-dropzone${dragging ? " is-dragging" : ""}`}
            onClick={() => picker.current?.click()}
            onDragOver={(event) => {
              event.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(event) => {
              event.preventDefault();
              setDragging(false);
              loadFile(event.dataTransfer.files?.[0]);
            }}
          >
            <span className="ops-upload-icon">↑</span>
            <strong>Drop your incident report here</strong>
            <span>
              or <u>browse files</u>
            </span>
            <small>
              TXT, Markdown, CSV, or LOG files, up to 1 MB
            </small>
          </button>

          <input
            ref={picker}
            className="ops-hidden-input"
            type="file"
            accept=".md,.txt,.csv,.log,text/markdown,text/plain,text/csv"
            onChange={(event) => {
              loadFile(event.target.files?.[0]);
              event.target.value = "";
            }}
          />

          {error && (
            <p className="ops-error" role="alert">
              {error}
            </p>
          )}

          {markdown && (
            <div className="ops-preview">
              <div className="ops-preview-title">
                <div>
                  <strong>{fileName}</strong>
                  <small>Report loaded</small>
                </div>

                <button
                  type="button"
                  className="ops-text-button"
                  onClick={removeFile}
                >
                  Remove
                </button>
              </div>

              <label htmlFor="ops-service">Affected service</label>
              <input
                id="ops-service"
                className="ops-service-input"
                value={service}
                onChange={(event) => setService(event.target.value)}
                placeholder="e.g. payment-api"
                maxLength={120}
              />

              <label htmlFor="ops-report-preview">Report preview</label>
              <pre id="ops-report-preview" className="ops-markdown-preview">
                {markdown}
              </pre>

              <button
                type="button"
                className="ops-primary-button"
                onClick={startInvestigation}
                disabled={!selectedFile}
              >
                Start Investigation <span>→</span>
              </button>

              <p className="ops-disclaimer">
                The selected report will be uploaded to the OpsPilot backend
                for investigation. Report-derived evidence remains unverified
                until independently validated.
              </p>
            </div>
          )}

          {!markdown && (
            <p className="ops-required-note">
              Recommended: include symptoms, metrics, errors, and deployment details.
            </p>
          )}
        </section>
      </section>

      <section className="ops-how-section">
        <div className="ops-step-label">THE WORKFLOW</div>
        <h2>From incident report to investigation.</h2>

        <div className="ops-workflow-grid">
          <article>
            <span>01</span>
            <h3>Review the report</h3>
            <p>Upload an incident report and verify the affected service.</p>
          </article>

          <article>
            <span>02</span>
            <h3>Investigate evidence</h3>
            <p>Run the configured service investigation and retrieve findings.</p>
          </article>

          <article>
            <span>03</span>
            <h3>Choose next steps</h3>
            <p>
              Review metrics, likely causes, missing evidence, and runbook guidance.
            </p>
          </article>
        </div>
      </section>

      <footer className="ops-footer">
        <span>OpsPilot</span>
        <span>Evidence first. Human-directed action.</span>
      </footer>
    </main>
  );
}

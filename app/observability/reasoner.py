import json
import os
from typing import Any

from dotenv import load_dotenv
from google import genai

load_dotenv()


class GeminiRCAReasoner:
    """
    Uses Gemini to convert structured RCA evidence into a
    human-readable incident analysis.

    Important:
    - Gemini does not collect observability data.
    - Gemini does not execute remediation.
    - Gemini must reason only from the supplied investigation.
    - Deterministic RCA remains available if Gemini is unavailable.
    """

    def __init__(
        self,
        model: str = "gemini-3.6-flash",
    ):
        self.model = model

        api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GOOGLE_API_KEY is not configured."
            )

        self.client = genai.Client(
            api_key=api_key
        )

    def reason(self, investigation: dict[str, Any]) -> dict[str, Any]:
        """
        Convert structured investigation evidence into a
        human-readable RCA explanation.
        """

        prompt = self._build_prompt(investigation)

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )

        text = response.text or ""

        return {
            "status": "success",
            "model": self.model,
            "analysis": text.strip(),
        }

    @staticmethod
    def _build_prompt(
        investigation: dict[str, Any],
    ) -> str:

        evidence = {
            "service": investigation.get("service"),
            "investigation_window": investigation.get(
                "investigation_window"
            ),
            "investigation_summary": investigation.get(
                "investigation_summary"
            ),
            "rca_analysis": investigation.get(
                "rca_analysis"
            ),
        }

        evidence_json = json.dumps(
            evidence,
            indent=2,
            default=str,
        )

        return f"""
You are a production incident RCA analyst.

Analyze ONLY the evidence provided below.

Do not invent:
- metrics
- logs
- deployments
- database behavior
- execution plans
- indexes
- infrastructure conditions
- causal relationships

Clearly distinguish:

1. Observed facts
2. Correlated evidence
3. Likely root-cause hypothesis
4. Confidence
5. Missing evidence
6. Recommended next investigation steps

A recent deployment occurring before an incident is temporal
correlation, not automatically proof of causation.

Runbook guidance is guidance, not proof.

If important evidence is missing, explicitly say so.

Do not claim that a missing database index, query plan,
lock contention, CPU issue, or infrastructure problem exists
unless the supplied evidence explicitly proves it.

The system is READ-ONLY.

Do not recommend that the AI autonomously:
- deploy code
- rollback code
- restart services
- modify databases
- modify configuration

Such actions may be suggested only as human-approved remediation
considerations.

Return the result using exactly these sections:

Incident
Affected Service
Observed Evidence
Investigation
Likely Root Cause
Confidence
Limitations
Recommended Next Steps

Keep the explanation concise but technically specific.

Structured investigation evidence:

{evidence_json}
"""
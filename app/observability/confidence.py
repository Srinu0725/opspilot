from typing import Any


class ConfidenceCalibrator:
    """
    Calculates confidence for RCA hypotheses using observable
    evidence relationships.

    This is not a probability of correctness.
    The score represents confidence in the evidence-supported
    hypothesis given the available investigation data.
    """

    def calibrate(
        self,
        hypothesis: dict[str, Any],
        investigation: dict[str, Any],
    ) -> dict[str, Any]:

        score = 0.0
        reasons: list[str] = []
        limitations: list[str] = []

        summary = investigation.get(
            "investigation_summary",
            {},
        )

        anomalies = summary.get(
            "observed_anomalies",
            [],
        )

        logs = summary.get(
            "key_logs",
            [],
        )

        deployment = summary.get(
            "deployment_correlation",
        )

        missing = summary.get(
            "missing_evidence",
            [],
        )

        hypothesis_text = hypothesis.get(
            "hypothesis",
            "",
        ).lower()

        # --------------------------------------------------
        # 1. Strong metric evidence
        # --------------------------------------------------

        if anomalies:
            score += 0.20
            reasons.append(
                "Multiple anomalous metrics support the incident."
            )

        database_anomaly = any(
            item.get("metric_type") == "database_latency"
            for item in anomalies
        )

        latency_anomaly = any(
            item.get("metric_type") == "latency"
            for item in anomalies
        )

        if database_anomaly:
            score += 0.15
            reasons.append(
                "Database latency shows a significant anomaly."
            )

        if latency_anomaly:
            score += 0.15
            reasons.append(
                "API latency shows a significant anomaly."
            )

        # --------------------------------------------------
        # 2. Log correlation
        # --------------------------------------------------

        database_logs = [
            log
            for log in logs
            if (
                "database" in log.lower()
                or "payment_lookup" in log.lower()
            )
        ]

        if database_logs:
            score += 0.20
            reasons.append(
                "Application logs independently show "
                "database/query degradation."
            )

        # --------------------------------------------------
        # 3. Deployment correlation
        # --------------------------------------------------

        deployment_query_change = False

        if deployment:
            for change in deployment.get("changes", []):
                change_text = str(change).lower()

                if (
                    "query" in change_text
                    or "database" in change_text
                    or "payment" in change_text
                ):
                    deployment_query_change = True
                    break

        if deployment_query_change:
            score += 0.15
            reasons.append(
                "A recent deployment changed the affected "
                "payment/database query."
            )

        # --------------------------------------------------
        # 4. Missing evidence penalty
        # --------------------------------------------------

        if missing:
            penalty = min(
                0.05 * len(missing),
                0.20,
            )

            score -= penalty

            limitations.extend(missing)

        # --------------------------------------------------
        # 5. Prevent invalid range
        # --------------------------------------------------

        score = max(
            0.0,
            min(score, 1.0),
        )

        # --------------------------------------------------
        # 6. Confidence level
        # --------------------------------------------------

        if score >= 0.80:
            level = "HIGH"
        elif score >= 0.55:
            level = "MEDIUM"
        else:
            level = "LOW"

        return {
            "score": round(score, 2),
            "level": level,
            "hypothesis": hypothesis.get(
                "hypothesis"
            ),
            "reasons": reasons,
            "limitations": limitations,
        }
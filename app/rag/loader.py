from pathlib import Path


RUNBOOKS_DIR = Path("data/runbooks")


def load_runbook(service: str) -> str:
    """
    Load the runbook for a service.

    Currently reads Markdown files from the local runbooks directory.
    Later this can be replaced with Google Cloud Storage or another
    document source.
    """

    runbook_file = RUNBOOKS_DIR / f"{service}.md"

    if not runbook_file.exists():
        raise FileNotFoundError(
            f"No runbook found for service: {service}"
        )

    return runbook_file.read_text(encoding="utf-8")
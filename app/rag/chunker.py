import re
from dataclasses import dataclass


@dataclass
class DocumentChunk:
    """
    Represents a semantically meaningful section of a document.
    """

    content: str
    source: str
    service: str
    section: str


def chunk_markdown(
    text: str,
    source: str,
    service: str,
    max_chunk_size: int = 1200,
) -> list[DocumentChunk]:
    """
    Split Markdown documents into section-aware chunks.

    Instead of blindly splitting text by character count,
    this function preserves Markdown headings and sections.
    """

    if not text.strip():
        return []

    lines = text.splitlines()

    sections: list[tuple[str, list[str]]] = []

    current_section = "Introduction"
    current_lines: list[str] = []

    for line in lines:

        # Detect Markdown headings such as:
        # # Payment API
        # ## Database Latency
        # ### Recent Deployment

        if re.match(r"^#{1,6}\s+", line):

            if current_lines:
                sections.append(
                    (
                        current_section,
                        current_lines,
                    )
                )

            current_section = re.sub(
                r"^#{1,6}\s+",
                "",
                line,
            ).strip()

            current_lines = []

        else:
            current_lines.append(line)

    # Add final section
    if current_lines:
        sections.append(
            (
                current_section,
                current_lines,
            )
        )

    chunks: list[DocumentChunk] = []

    for section_name, section_lines in sections:

        section_text = "\n".join(
            section_lines
        ).strip()

        if not section_text:
            continue

        # If the section is small enough, keep it intact.
        if len(section_text) <= max_chunk_size:

            chunks.append(
                DocumentChunk(
                    content=section_text,
                    source=source,
                    service=service,
                    section=section_name,
                )
            )

            continue

        # Large sections are split while preserving
        # the section metadata.
        start = 0

        while start < len(section_text):

            end = min(
                start + max_chunk_size,
                len(section_text),
            )

            chunk_text = section_text[
                start:end
            ].strip()

            if chunk_text:

                chunks.append(
                    DocumentChunk(
                        content=chunk_text,
                        source=source,
                        service=service,
                        section=section_name,
                    )
                )

            if end >= len(section_text):
                break

            start = end

    return chunks


# Keep the old function available for compatibility.
def chunk_text(
    text: str,
    chunk_size: int = 800,
    chunk_overlap: int = 100,
) -> list[str]:
    """
    Legacy character-based chunking function.

    Kept temporarily so existing code does not break.
    New RAG code should use chunk_markdown().
    """

    if not text.strip():
        return []

    if chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be smaller than chunk_size"
        )

    chunks = []

    start = 0
    text_length = len(text)

    while start < text_length:

        end = min(
            start + chunk_size,
            text_length,
        )

        chunk = text[
            start:end
        ].strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start = end - chunk_overlap

    return chunks
import re
from pathlib import Path


def load_documents(folder):
    """Read every .md file in the folder into a list of {source, text}."""
    documents = []
    for path in sorted(Path(folder).glob("*.md")):
        text = path.read_text(encoding="utf-8")
        documents.append({"source": path.name, "text": text})

    return documents

def merge_headings(paragraphs):
    """Attach each heading to the paragraph beneath it, so a heading is
    never a standalone unit that can dangle at a chunk boundary."""
    merged = []
    pending = None

    for para in paragraphs:
        if para.lstrip().startswith("#"):     # it's a heading
            pending = para if pending is None else pending + "\n" + para
            continue

        if pending:
            merged.append(pending + "\n\n" + para)    # heading + its body
            pending = None
        else:
            merged.append(para)

    if pending:
        merged.append(pending)

    return merged

def last_sentence(text):
    """Return the final sentence of a chunk, to carry over as real overlap."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return sentences[-1] if sentences else ""

def chunk_text(text, target_size=500):
    """
    Split one document into chunks.

    Strategy: split on blank lines first, so we cut along paragraph 
    boundaries (the document's natural seams) instead of blindly every
    N characters. We then glue paragraphs together until a chunk is about
    `target_size` characters and start a new chunk when adding the next
    paragraph would push us over.

    Overlap: When we start a new chunk, we carry over the LAST paragraph
    of the previous chunk, so an idea that spans a boundary isn't severed.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    units = merge_headings(paragraphs)
    # print(units)

    chunks = []
    current = []       # paragraphs in the chunk we're building
    current_len = 0

    for unit in units:
        # If adding this paragraph overflows AND we already have content,
        # close off the current chunk first.
        if current_len + len(unit) > target_size and current:
            # chunks.append("\n\n".join(current))
            # # Start the next chunk by carrying over the last paragraph
            # # (this is our overlap).
            # current = [current[-1]]
            # current_len = len(current[-1])
            chunk = "\n\n".join(current)
            chunks.append(chunk)
            carry = last_sentence(chunk)         # overlap = last real sentence
            current = [carry]
            current_len = len(carry)
        
        current.append(unit)
        current_len += len(unit)

    # Don't forget the final chunk still being built.
    if current:
        chunks.append("\n\n".join(current))
    # print(len(chunks))

    return chunks

def chunk_documents(documents, target_size=500):
    """chunk every document, tagging each chunck with its source file."""
    all_chunks = []

    for doc in documents:
        for i, chunk in enumerate(chunk_text(doc["text"], target_size)):
            all_chunks.append({
                "source": doc["source"],
                "chunk_index": i,
                "text": chunk
            })

    return all_chunks

if __name__ == "__main__":
    from app.config import settings

    docs = load_documents(settings.docs_folder)
    chunks = chunk_documents(docs, target_size=settings.chunk_size)

    print(f"Loaded {len(docs)} documents")
    print(f"Produced {len(chunks)} chunks\n")

    # Print the first few chunks so we can eyeball their quality.
    for chunk in chunks[:4]:
        print("─" * 60)
        print(f"source: {chunk['source']}  |  chunk #{chunk['chunk_index']}")
        print(f"length: {len(chunk['text'])} chars")
        print(chunk["text"])
        print()
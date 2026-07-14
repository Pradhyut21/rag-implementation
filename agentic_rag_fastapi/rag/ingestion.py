from docx import Document
from pypdf import PdfReader
from nltk.tokenize import sent_tokenize

def load_docx(file_path: str) -> str:
    doc = Document(file_path)
    text = []
    for para in doc.paragraphs:
        if para.text.strip():
            text.append(para.text.strip())
    return "\n".join(text)

def load_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    pages = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        if page_text.strip():
            pages.append(page_text.strip())
    return "\n".join(pages)

def load_document(file_path: str) -> str:
    file_path_lower = file_path.lower()

    if file_path_lower.endswith(".docx"):
        return load_docx(file_path)
    elif file_path_lower.endswith(".pdf"):
        return load_pdf(file_path)
    else:
        raise ValueError("Unsupported file type. Only .docx and .pdf are supported.")

def chunk_text(text: str, chunk_size: int = 6, overlap: int = 2):
    """
    Splits text into sentence-based chunks.
    chunk_size = number of sentences per chunk
    overlap = overlapping sentences between chunks
    """
    sentences = sent_tokenize(text)
    chunks = []

    start = 0
    while start < len(sentences):
        end = min(start + chunk_size, len(sentences))
        chunk = " ".join(sentences[start:end]).strip()
        if chunk:
            chunks.append(chunk)

        if end == len(sentences):
            break

        start += chunk_size - overlap

    return chunks

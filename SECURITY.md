# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 3.x (main) | ✅ Actively maintained |
| 2.x | ⚠️ Security fixes only |
| < 2.0 | ❌ Unsupported |

---

## Reporting a Vulnerability

**Please do NOT open a public GitHub issue for security vulnerabilities.**

Report security issues privately via **GitHub's private vulnerability reporting**:

1. Go to the [Security tab](../../security) of this repository
2. Click **"Report a vulnerability"**
3. Fill in the template with as much detail as possible

We will acknowledge your report within **48 hours** and provide a timeline for a fix.

### What to include

- Affected component (API, auth, file upload, etc.)
- Description of the vulnerability and potential impact
- Steps to reproduce
- Suggested fix (if you have one)

---

## Security Architecture

### Authentication
- All write endpoints (`POST /upload-doc`, `DELETE /documents/{id}`, query endpoints) require the `X-API-Key` header
- Default demo key `demo-rag-2026` — **must be changed before production deployment**
- Set via `API_KEY` environment variable

### Rate Limiting
- Query endpoints: 30 requests/minute per IP
- Upload endpoints: 20 requests/hour per IP
- Implemented via [slowapi](https://github.com/laurentS/slowapi)

### Input Validation
- Queries limited to 2000 characters
- File uploads validated by extension + PDF magic bytes
- File size limited to configurable `MAX_FILE_SIZE_MB` (default 20MB)
- Filenames sanitised with `os.path.basename()` to prevent directory traversal

### CORS
- Restricted to `ALLOWED_ORIGINS` environment variable (no wildcard `*` in production)
- Default: `http://localhost:5173,http://localhost:3000`

### File System
- Registry writes use atomic `os.replace()` to prevent corruption under concurrent access
- In-memory VectorStore cache protected by `threading.Lock()`

### Dependency Management
- Dependencies scanned weekly by [Safety](https://pyup.io/safety/) via CI
- [Bandit](https://bandit.readthedocs.io/) SAST runs on every push
- [CodeQL](https://codeql.github.com/) Advanced Security scans Python and JavaScript

---

## Known Security Limitations

> The following are **by design** for the hackathon/demo context, but must be addressed before production deployment:

| Limitation | Risk | Remediation |
|------------|------|-------------|
| Single shared API key | Medium | Migrate to JWT per-user auth |
| SQLite observability DB | Low | Migrate to PostgreSQL for multi-process safety |
| Local FAISS file storage | Medium | Migrate to cloud vector store (Pinecone, pgvector) |
| No input sanitization beyond length | Low | Add semantic content filtering |

---

## Disclosure Policy

Once a vulnerability is confirmed and fixed, we will:

1. Release a patched version
2. Add a note to [CHANGELOG.md](CHANGELOG.md)
3. Credit the reporter in the release notes (if they consent)

We aim for a **90-day disclosure timeline** from report to public disclosure.

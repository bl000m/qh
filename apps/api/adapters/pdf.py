"""Bounded local PDF extraction in a disposable, resource-limited child process."""
import asyncio
import json
import os
import sys

from app.understanding.documents import DocumentInvalid, MAX_PDF_BYTES

# No provider credentials, network clients, JavaScript or attachment execution.
_WORKER = r"""
import io, json, logging, resource, sys
resource.setrlimit(resource.RLIMIT_AS, (384*1024*1024, 384*1024*1024))
resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
logging.disable(logging.CRITICAL)
from pypdf import PdfReader
try:
    reader = PdfReader(io.BytesIO(sys.stdin.buffer.read(3145729)), strict=True)
    if reader.is_encrypted:
        raise ValueError('password')
    if not 1 <= len(reader.pages) <= 500:
        raise ValueError('resources')
    pages, size = [], 0
    for page in reader.pages:
        text = page.extract_text() or ''
        size += len(text.encode())
        if size > 500000 or '\x00' in text:
            raise ValueError('resources')
        pages.append(text)
    if not any(t.strip() for t in pages):
        raise ValueError('no_text')
    print(json.dumps(dict(pages=pages), ensure_ascii=True))
except ValueError as exc:
    code = str(exc) if str(exc) in ('password','resources','no_text') else 'corrupt'
    print(json.dumps(dict(error=code)))
except Exception:
    print(json.dumps(dict(error='corrupt')))
"""
_ERRORS = dict(password='PDF protégé par mot de passe : import impossible.',
    resources='PDF trop complexe ou texte trop volumineux pour cette version.',
    no_text='Ce PDF ne contient aucun texte extractible. Les documents scannés nécessitent un OCR, indisponible ici.',
    corrupt='PDF corrompu ou non pris en charge.')
# Bound concurrent CPU/memory use for hostile uploads.
_slots = asyncio.Semaphore(2)


async def extract_pdf(data):
    if not data or len(data)>MAX_PDF_BYTES:
        raise DocumentInvalid('Le PDF doit faire au maximum 3 MiB (3 145 728 octets).')
    if not data.startswith(b'%PDF-'):
        raise DocumentInvalid(_ERRORS['corrupt'])
    async with _slots:
        process = await asyncio.create_subprocess_exec(sys.executable, '-I', '-c', _WORKER,
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL, cwd='/tmp',
            env={'PATH':os.defpath, 'PYTHONIOENCODING':'utf-8'})
        try:
            stdout, _ = await asyncio.wait_for(process.communicate(data), timeout=15)
        except (TimeoutError, asyncio.CancelledError) as exc:
            if process.returncode is None:
                process.kill()
            await process.wait()
            if isinstance(exc,asyncio.CancelledError):
                raise
            raise DocumentInvalid(_ERRORS['resources']) from None
    if process.returncode or len(stdout)>3100000:
        raise DocumentInvalid(_ERRORS['resources'])
    try:
        result=json.loads(stdout)
        if 'error' in result:
            raise DocumentInvalid(_ERRORS[result['error']])
        return result['pages']
    except (KeyError, json.JSONDecodeError):
        raise DocumentInvalid(_ERRORS['corrupt']) from None

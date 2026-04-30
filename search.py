import re
import subprocess
import unicodedata
from pathlib import Path

try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


def _extract_pdf_text(path: str) -> str:
    for binary in ["pdftotext", "/opt/homebrew/bin/pdftotext"]:
        result = subprocess.run(
            [binary, path, "-"],
            capture_output=True, text=True, encoding="utf-8"
        )
        if result.returncode == 0:
            return result.stdout
    return ""


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    return re.sub(r"[^a-z0-9ąćęłńóśźż\s]", "", text.lower())


def _split_chunks(text: str, chunk_size: int = 900, overlap: int = 200) -> list:
    """
    Splits PDF text into overlapping chunks, keeping section headers attached
    to the content below them.
    """
    lines = text.split("\n")
    paragraphs = []
    current = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current:
                paragraphs.append(" ".join(current))
                current = []
        else:
            current.append(stripped)
    if current:
        paragraphs.append(" ".join(current))

    chunks = []
    current_chunk = ""
    for para in paragraphs:
        if not para or len(para) < 5:
            continue
        if len(current_chunk) + len(para) + 2 > chunk_size:
            if current_chunk:
                chunks.append(current_chunk.strip())
                # keep tail for overlap
                words = current_chunk.split()
                tail_words = words[-40:] if len(words) > 40 else words
                current_chunk = " ".join(tail_words) + "\n" + para
            else:
                chunks.append(para[:chunk_size])
                current_chunk = para[chunk_size - overlap:]
        else:
            current_chunk = (current_chunk + "\n" + para) if current_chunk else para
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    return chunks


STOPWORDS = {
    "co", "jak", "ile", "czy", "gdzie", "kiedy", "kto", "ktory", "ktora",
    "jakie", "jakich", "jakim", "jakiego", "jaka", "jaką",
    "w", "z", "do", "na", "po", "od", "za", "dla", "przez", "przy",
    "o", "a", "i", "lub", "albo", "ze", "sie", "to", "nie",
    "jest", "sa", "ma", "mam", "miec", "mozna", "moze",
    "mi", "mu", "go", "ten", "ta", "te", "tego", "tej",
    "byl", "byla", "bylo", "być", "byc",
}


def _extract_keywords(query: str) -> list:
    words = re.findall(r"[a-ząćęłńóśźżA-ZĄĆĘŁŃÓŚŹŻ]{3,}", query)
    norm = [_normalize(w) for w in words]
    filtered = [w for w in norm if w not in STOPWORDS and len(w) >= 3]
    stems = set()
    for w in filtered:
        stems.add(w)
        if len(w) >= 7:
            stems.add(w[:6])
        if len(w) >= 6:
            stems.add(w[:5])
        if len(w) >= 5:
            stems.add(w[:4])
    return list(stems)


def _score_chunk(chunk: str, keywords: list) -> float:
    norm = _normalize(chunk)
    score = 0.0
    for kw in keywords:
        count = norm.count(kw)
        if count > 0:
            # bonus for exact longer match
            weight = 1.0 + (len(kw) - 3) * 0.1
            score += weight + count * 0.2
    return score


class StatutSearch:
    def __init__(self, files: dict):
        self.docs: dict = {}
        for name, path in files.items():
            if Path(path).exists():
                text = _extract_pdf_text(path)
                chunks = _split_chunks(text)
                self.docs[name] = chunks
                print(f"Załadowano {name}: {len(chunks)} fragmentów")
            else:
                print(f"UWAGA: Nie znaleziono pliku {path}")

    def search(self, query: str, top_k: int = 5) -> list:
        keywords = _extract_keywords(query)
        results = []
        for doc_name, chunks in self.docs.items():
            for chunk in chunks:
                score = _score_chunk(chunk, keywords)
                if score > 0:
                    results.append({"score": score, "text": chunk, "doc": doc_name})
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    async def odpowiedz(self, query: str, gemini_key: str = None) -> dict:
        hits = self.search(query, top_k=5)

        if not hits:
            return {
                "odpowiedz": (
                    "Nie znalazłem nic pasującego w statucie. "
                    "Spróbuj użyć innych słów kluczowych."
                ),
                "zrodlo": "—",
            }

        context = "\n\n---\n\n".join(h["text"] for h in hits)
        sources = list(dict.fromkeys(h["doc"] for h in hits))
        source_str = ", ".join(sources)

        if gemini_key and GEMINI_AVAILABLE:
            try:
                answer = await _ask_gemini(gemini_key, query, context)
                return {"odpowiedz": answer, "zrodlo": source_str}
            except Exception as e:
                print(f"Gemini error: {e}")

        # fallback: wyciągnij najbardziej trafne zdania z najlepszego fragmentu
        cytat = _wyciagnij_cytat(hits[0]["text"], _extract_keywords(query))
        return {
            "odpowiedz": f"> {cytat}",
            "zrodlo": source_str,
        }


def _wyciagnij_cytat(chunk: str, keywords: list, max_len: int = 400) -> str:
    """Zwraca 1-3 najlepiej pasujące zdania z fragmentu zamiast całego bloku."""
    # podziel na zdania
    zdania = re.split(r"(?<=[.!?;])\s+", chunk)
    scored = []
    for z in zdania:
        z = z.strip()
        if len(z) < 15:
            continue
        sc = sum(1 for kw in keywords if kw in _normalize(z))
        scored.append((sc, z))
    scored.sort(key=lambda x: x[0], reverse=True)

    # weź najlepsze zdania mieszczące się w limicie
    result = []
    total = 0
    for sc, z in scored:
        if sc == 0 and result:
            break
        if total + len(z) > max_len and result:
            break
        result.append(z)
        total += len(z)
        if len(result) >= 3:
            break

    if not result:
        return chunk[:max_len] + ("…" if len(chunk) > max_len else "")
    return " ".join(result)


async def _ask_gemini(api_key: str, query: str, context: str) -> str:
    client = genai.Client(api_key=api_key)

    prompt = f"""Jesteś pomocnym asystentem szkolnym. Odpowiadasz na pytania uczniów o statucie szkoły.

ZASADY:
- Odpowiedź max 3 zdania – krótko i konkretnie.
- Potem dodaj JEDEN dokładny cytat ze statutu (zacytuj dosłownie, bez skracania) poprzedzony słowem „Cytat:".
- Jeśli pytanie dotyczy listy (np. prawa ucznia), podaj listę punktów, ale bez przytaczania całego rozdziału.
- Jeśli odpowiedzi nie ma w podanych fragmentach, napisz tylko: „Nie znalazłem tej informacji w statucie."
- Nie wymyślaj, nie dodawaj nic spoza statutu.

FRAGMENTY STATUTU:
{context[:3500]}

PYTANIE: {query}

ODPOWIEDŹ:"""

    response = await client.aio.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )
    return response.text.strip()

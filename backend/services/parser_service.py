import re
from datetime import datetime
from typing import Dict


def parse_txt(content: str) -> Dict:
    """Parse a plain text transcript file."""
    lines = content.strip().split('\n')
    speakers = set()
    segments = []
    current_speaker = None
    current_text = []

    speaker_pattern = re.compile(
        r'^(?:\[?\d{1,2}:\d{2}(?::\d{2})?\]?\s*)?'
        r'([A-Z][a-zA-Z\s]+?)(?:\s*[:]\s*)(.*)'
    )

    for line in lines:
        line = line.strip()
        if not line:
            if current_speaker and current_text:
                segments.append({"speaker": current_speaker, "text": ' '.join(current_text)})
                current_text = []
            continue

        match = speaker_pattern.match(line)
        if match:
            if current_speaker and current_text:
                segments.append({"speaker": current_speaker, "text": ' '.join(current_text)})
                current_text = []
            current_speaker = match.group(1).strip()
            speakers.add(current_speaker)
            remaining = match.group(2).strip()
            if remaining:
                current_text.append(remaining)
        else:
            current_text.append(line)

    if current_speaker and current_text:
        segments.append({"speaker": current_speaker, "text": ' '.join(current_text)})

    # Fallback: if no speakers detected, split by paragraphs
    if not segments:
        paragraphs = re.split(r'\n\s*\n', content.strip())
        for i, para in enumerate(paragraphs):
            if para.strip():
                segments.append({"speaker": f"Speaker {i+1}", "text": para.strip()})
                speakers.add(f"Speaker {i+1}")

    full_text = content.strip()
    return {
        "raw_text": full_text,
        "segments": segments,
        "speaker_count": len(speakers),
        "word_count": len(full_text.split()),
        "meeting_date": detect_meeting_date(content),
        "speakers": list(speakers),
    }


def parse_vtt(content: str) -> Dict:
    """Parse a WebVTT format transcript."""
    lines = content.strip().split('\n')
    speakers = set()
    segments = []
    current_text = []
    current_speaker = None

    i = 0
    # Skip WEBVTT header lines
    while i < len(lines) and not re.match(r'\d{2}:\d{2}', lines[i].strip()):
        i += 1

    ts_pat = re.compile(r'\d{2}:\d{2}[:.]\d{3}\s*-->\s*\d{2}:\d{2}[:.]\d{3}')
    voice_pat = re.compile(r'<v\s+([^>]+)>(.*)')
    colon_pat = re.compile(r'^([A-Z][a-zA-Z\s]+?):\s*(.*)')

    while i < len(lines):
        line = lines[i].strip()

        if re.match(r'^\d+$', line):
            i += 1
            continue

        if ts_pat.match(line):
            if current_speaker and current_text:
                segments.append({"speaker": current_speaker, "text": ' '.join(current_text)})
                current_text = []
            i += 1
            continue

        if not line:
            if current_speaker and current_text:
                segments.append({"speaker": current_speaker, "text": ' '.join(current_text)})
                current_text = []
                current_speaker = None
            i += 1
            continue

        vm = voice_pat.match(line)
        if vm:
            current_speaker = vm.group(1).strip()
            speakers.add(current_speaker)
            txt = re.sub(r'</v>', '', vm.group(2)).strip()
            if txt:
                current_text.append(txt)
            i += 1
            continue

        cm = colon_pat.match(line)
        if cm:
            current_speaker = cm.group(1).strip()
            speakers.add(current_speaker)
            txt = cm.group(2).strip()
            if txt:
                current_text.append(txt)
            i += 1
            continue

        if current_speaker is None:
            current_speaker = "Unknown"
            speakers.add(current_speaker)
        current_text.append(line)
        i += 1

    if current_speaker and current_text:
        segments.append({"speaker": current_speaker, "text": ' '.join(current_text)})

    full_text = '\n'.join(f"{s['speaker']}: {s['text']}" for s in segments)
    word_count = sum(len(s["text"].split()) for s in segments)

    return {
        "raw_text": full_text,
        "segments": segments,
        "speaker_count": len(speakers),
        "word_count": word_count,
        "meeting_date": detect_meeting_date(content),
        "speakers": list(speakers),
    }


def detect_meeting_date(text: str):
    """Try to extract a date from the first 500 chars of the transcript."""
    patterns = [
        (r'(\d{4}-\d{2}-\d{2})', '%Y-%m-%d'),
        (r'(\d{1,2}/\d{1,2}/\d{4})', '%m/%d/%Y'),
        (r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})', None),
    ]
    header = text[:500]
    for pat, fmt in patterns:
        m = re.search(pat, header, re.IGNORECASE)
        if m:
            ds = m.group(1).replace(',', '')
            if fmt:
                try:
                    return datetime.strptime(ds, fmt).date()
                except ValueError:
                    continue
            else:
                for f in ('%B %d %Y', '%B %d %Y', '%d %B %Y'):
                    try:
                        return datetime.strptime(ds, f).date()
                    except ValueError:
                        continue
    return None

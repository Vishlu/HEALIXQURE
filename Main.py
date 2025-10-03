# # debug_scanner.py
# import cv2
# from pyzbar.pyzbar import decode as zbar_decode
# from datetime import datetime
# import sys

# def try_decode(frame):
#     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#     r = zbar_decode(gray)
#     if r:
#         try:
#             return r[0].data.decode('utf-8', errors='ignore')
#         except:
#             return str(r[0].data)
#     # fallback opencv
#     qrd = cv2.QRCodeDetector()
#     data, pts, _ = qrd.detectAndDecode(frame)
#     if data:
#         return data
#     return None

# def main():
#     cap = None
#     # try several indices/backends
#     for idx in [0, 1, 2]:
#         for backend in [cv2.CAP_DSHOW, None]:
#             try:
#                 cap = cv2.VideoCapture(idx, backend) if backend else cv2.VideoCapture(idx)
#                 if cap.isOpened():
#                     print("Using camera index", idx, "backend", backend)
#                     break
#                 else:
#                     cap.release()
#             except Exception:
#                 pass
#         if cap and cap.isOpened():
#             break
#     if not cap or not cap.isOpened():
#         print("camera open failed; try different index or CAP_DSHOW")
#         sys.exit(1)

#     while True:
#         ok, frame = cap.read()
#         if not ok:
#             break
#         payload = try_decode(frame)
#         if payload:
#             print("DETECTED payload (repr):", repr(payload))
#         cv2.imshow("debug", frame)
#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break
#     cap.release()
#     cv2.destroyAllWindows()

# if __name__ == '__main__':
#     main()





# # debug_scanner_with_parse.py
# import cv2
# from pyzbar.pyzbar import decode as zbar_decode
# from datetime import datetime, date
# import sys
# import re

# # -----------------------
# # Helper: GS1 parsing & validity
# # -----------------------
# AI_MAPPING = {
#     '01': ('gtin', 14, True),   # GTIN fixed 14
#     '17': ('expiry', 6, True),  # expiry YYMMDD
#     '10': ('batch', None, False),  # batch variable
#     '21': ('serial', None, False), # serial variable
# }

# def format_expiry(expiry_raw):
#     if not expiry_raw:
#         return None
#     s = re.sub(r'\D', '', expiry_raw)
#     try:
#         if len(s) == 6:
#             return datetime.strptime(s, '%y%m%d').date().isoformat()
#         if len(s) == 8:
#             return datetime.strptime(s, '%Y%m%d').date().isoformat()
#     except Exception:
#         return None
#     return None

# def check_validity(expiry_iso):
#     if not expiry_iso:
#         return "UNKNOWN"
#     try:
#         d = datetime.strptime(expiry_iso, '%Y-%m-%d').date()
#         return "VALID" if d >= date.today() else "EXPIRED"
#     except Exception:
#         return "UNKNOWN"

# def normalize_gtin(g):
#     """Return GTIN-14 normalized value if input looks like a UPC/EAN."""
#     if not g:
#         return None
#     digits = re.sub(r'\D', '', str(g))
#     if len(digits) == 14:
#         return digits
#     if len(digits) == 13:
#         return '0' + digits
#     if len(digits) == 12:
#         return '00' + digits
#     # fallback: return raw digits if unknown length
#     return digits if digits else None

# def parse_parenthesis_form(s):
#     """Parse (01)....(17).... style."""
#     res = {}
#     for ai, val in re.findall(r'\((\d{2,3})\)([^\(]+)', s):
#         if ai in AI_MAPPING:
#             name, _, _ = AI_MAPPING[ai]
#             res[name] = val
#     if 'expiry' in res:
#         res['expiry_formatted'] = format_expiry(res['expiry'])
#     if 'gtin' in res:
#         res['gtin'] = normalize_gtin(res.get('gtin'))
#     return res

# def parse_gs1_data(raw):
#     """Robust-ish GS1 parser:
#        - if payload is simple numeric (12/13/14), treat as GTIN
#        - handle concatenated AIs and group separator (\x1D)
#        - handle parenthesis (01) format
#     """
#     if not raw:
#         return {}

#     data = raw

#     # normalize common escapes into real GS char
#     data = data.replace('\\x1D', '\x1D').replace('\\u001d', '\x1D').replace('|GS|', '\x1D')
#     data = re.sub(r'^\]d2?', '', data, flags=re.IGNORECASE)  # remove ]d or ]d2 prefix if present

#     # If it's just digits (UPC/EAN) — handle as GTIN-like value
#     digits_only = re.sub(r'\D', '', data)
#     if digits_only and len(digits_only) in (12, 13, 14):
#         gt = normalize_gtin(digits_only)
#         return {'gtin': gt, 'expiry_formatted': None, 'batch': None, 'serial': None}

#     # parenthesis format?
#     if data.startswith('('):
#         parsed = parse_parenthesis_form(data)
#         # ensure gtin normalization if present
#         if 'gtin' in parsed:
#             parsed['gtin'] = normalize_gtin(parsed['gtin'])
#         return parsed

#     # split by GS (ASCII 29)
#     segments = re.split(r'\x1D', data)
#     result = {}
#     for seg in segments:
#         seg = seg.strip()
#         if not seg:
#             continue
#         i = 0
#         L = len(seg)
#         while i + 2 <= L:
#             ai = seg[i:i+2]
#             if ai in AI_MAPPING:
#                 name, length, fixed = AI_MAPPING[ai]
#                 i += 2
#                 if fixed and length:
#                     # fixed length field
#                     if i + length <= L:
#                         val = seg[i:i+length]
#                         i += length
#                     else:
#                         # truncated; take remainder
#                         val = seg[i:]
#                         i = L
#                 else:
#                     # variable: read until next AI or end
#                     # find next AI occurrence
#                     next_match = re.search(r'(' + '|'.join(AI_MAPPING.keys()) + r')', seg[i:])
#                     if next_match:
#                         next_pos = i + next_match.start()
#                         val = seg[i:next_pos]
#                         i = next_pos
#                     else:
#                         val = seg[i:]
#                         i = L
#                 if val:
#                     result[name] = val
#             else:
#                 # no known AI at this position, advance 1 char
#                 i += 1

#     # post-process expiry and gtin
#     if 'expiry' in result and 'expiry_formatted' not in result:
#         result['expiry_formatted'] = format_expiry(result['expiry'])
#     if 'gtin' in result:
#         result['gtin'] = normalize_gtin(result.get('gtin'))
#     return result

# # -----------------------
# # Original detector code (kept structure intact)
# # -----------------------
# def try_decode(frame):
#     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#     r = zbar_decode(gray)
#     if r:
#         try:
#             return r[0].data.decode('utf-8', errors='ignore')
#         except:
#             return str(r[0].data)
#     # fallback opencv
#     qrd = cv2.QRCodeDetector()
#     data, pts, _ = qrd.detectAndDecode(frame)
#     if data:
#         return data
#     return None

# def main():
#     cap = None
#     # try several indices/backends
#     for idx in [0, 1, 2]:
#         for backend in [cv2.CAP_DSHOW, None]:
#             try:
#                 cap = cv2.VideoCapture(idx, backend) if backend else cv2.VideoCapture(idx)
#                 if cap.isOpened():
#                     print("Using camera index", idx, "backend", backend)
#                     break
#                 else:
#                     cap.release()
#             except Exception:
#                 pass
#         if cap and cap.isOpened():
#             break
#     if not cap or not cap.isOpened():
#         print("camera open failed; try different index or CAP_DSHOW")
#         sys.exit(1)

#     while True:
#         ok, frame = cap.read()
#         if not ok:
#             break
#         payload = try_decode(frame)
#         if payload:
#             # existing debug print
#             print("DETECTED payload (repr):", repr(payload))

#             # NEW: parse payload and print required fields
#             parsed = parse_gs1_data(payload)
#             gtin = parsed.get('gtin')
#             expiry_iso = parsed.get('expiry_formatted')
#             batch = parsed.get('batch')
#             serial = parsed.get('serial')
#             status = check_validity(expiry_iso)

#             parsed_output = {
#                 'scheme': 'GS1',
#                 'gtin': gtin,
#                 'expiry': expiry_iso,
#                 'batch': batch,
#                 'serial': serial,
#                 'status': status
#             }

#             print("PARSED ->", parsed_output)

#         cv2.imshow("debug", frame)
#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break
#     cap.release()
#     cv2.destroyAllWindows()

# if __name__ == '__main__':
#     main()




#!/usr/bin/env python3
"""
medicine_scanner_full.py

Real-time scanner that:
- decodes barcodes/QR codes using pyzbar (and OpenCV fallback),
- interprets payloads as EAN/UPC, GS1 (AIs), URLs, or small XML-like payloads,
- extracts GTIN, expiry, batch, serial where available,
- prints parsed dictionary to terminal and overlays info on camera feed.

Run: python medicine_scanner_full.py
"""

import cv2
from pyzbar.pyzbar import decode as zbar_decode
from datetime import datetime, date
import re
import sys
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

# --- GS1 AI map (we only care about these AIs) ---
AI_MAPPING = {
    '01': ('gtin', 14, True),   # GTIN fixed 14
    '17': ('expiry', 6, True),  # Expiry YYMMDD (or sometimes YYYYMMDD)
    '10': ('batch', None, False),  # Batch/Lot - variable
    '21': ('serial', None, False)  # Serial - variable
}


# --- Helpers: expiry formatting, validity, GTIN normalization ---
def format_expiry(expiry_raw):
    if not expiry_raw:
        return None
    s = re.sub(r'\D', '', expiry_raw)
    try:
        if len(s) == 6:  # YYMMDD
            return datetime.strptime(s, '%y%m%d').date().isoformat()
        if len(s) == 8:  # YYYYMMDD
            return datetime.strptime(s, '%Y%m%d').date().isoformat()
    except Exception:
        return None
    return None


def check_validity(expiry_iso):
    if not expiry_iso:
        return "UNKNOWN"
    try:
        d = datetime.strptime(expiry_iso, '%Y-%m-%d').date()
        return "VALID" if d >= date.today() else "EXPIRED"
    except Exception:
        return "UNKNOWN"


def normalize_gtin(g):
    """Normalize 12/13/14-digit codes to GTIN-14 string (prefixed with zeros if needed)."""
    if not g:
        return None
    digits = re.sub(r'\D', '', str(g))
    if len(digits) == 14:
        return digits
    if len(digits) == 13:
        return '0' + digits
    if len(digits) == 12:
        return '00' + digits
    return digits if digits else None


# --- GS1 parser (robust-ish) ---
def parse_parenthesis_form(s):
    """Parse (AI)value(AI)value forms like (01)....(17)...."""
    res = {}
    for ai, val in re.findall(r'\((\d{2,3})\)([^\(]+)', s):
        if ai in AI_MAPPING:
            name, _, _ = AI_MAPPING[ai]
            res[name] = val
    if 'expiry' in res:
        res['expiry_formatted'] = format_expiry(res['expiry'])
    if 'gtin' in res:
        res['gtin'] = normalize_gtin(res.get('gtin'))
    return res


def parse_gs1_data(raw):
    """
    Parse concatenated GS1 AIs in payloads. Handles:
    - leading ]d or ]d2
    - group separators (\x1D or literal forms)
    - both concatenated and segment-by-segment forms
    Returns dict with keys like gtin, expiry, batch, serial, expiry_formatted
    """
    if not raw:
        return {}

    data = raw

    # Normalize various escaped GS representations to actual ASCII 29
    data = data.replace('\\x1D', '\x1D').replace('\\u001d', '\x1D').replace('|GS|', '\x1D')
    data = data.replace('\u001d', '\x1D')  # just in case
    data = re.sub(r'^\]d2?', '', data, flags=re.IGNORECASE)  # remove leading ]d or ]d2

    # If it's parenthesis format, parse using that route
    if data.startswith('('):
        return parse_parenthesis_form(data)

    # Split on GS (ASCII 29). Each segment might contain concatenated AIs.
    segments = re.split(r'\x1D', data)
    result = {}
    for seg in segments:
        seg = seg.strip()
        if not seg:
            continue
        i = 0
        L = len(seg)
        while i + 2 <= L:
            ai = seg[i:i+2]
            if ai in AI_MAPPING:
                name, length, fixed = AI_MAPPING[ai]
                i += 2
                if fixed and length:
                    if i + length <= L:
                        val = seg[i:i+length]
                        i += length
                    else:
                        # truncated; take remainder
                        val = seg[i:]
                        i = L
                else:
                    # variable: read until next AI or end
                    next_match = re.search(r'(' + '|'.join(AI_MAPPING.keys()) + r')', seg[i:])
                    if next_match:
                        next_pos = i + next_match.start()
                        val = seg[i:next_pos]
                        i = next_pos
                    else:
                        val = seg[i:]
                        i = L
                if val:
                    result[name] = val
            else:
                i += 1

    if 'expiry' in result and 'expiry_formatted' not in result:
        result['expiry_formatted'] = format_expiry(result['expiry'])
    if 'gtin' in result:
        result['gtin'] = normalize_gtin(result.get('gtin'))
    return result


# --- Payload interpreter: classify & parse various payload types ---
def interpret_payload(payload):
    """
    Return a normalized dict:
      - scheme: 'GS1' | 'EAN/UPC' | 'URL' | 'CUSTOM_XML' | 'RAW'
      - gtin, expiry_formatted, batch, serial
      - extra: additional info (e.g., parsed XML fields, URL)
    """
    p = payload.strip()
    # 1) URL
    low = p.lower()
    if low.startswith('http://') or low.startswith('https://'):
        return {'scheme': 'URL', 'gtin': None, 'expiry_formatted': None, 'batch': None, 'serial': None,
                'extra': {'url': p}}

    # 2) XML / HTML-like small payloads
    if p.startswith('<') and p.endswith('>'):
        extra = {}
        try:
            root = ET.fromstring(p)
            # collect tag->text for children
            for child in root:
                tag = child.tag.strip()
                text = child.text.strip() if child.text else ''
                extra[tag] = text
        except Exception as e:
            extra['xml_error'] = str(e)
        return {'scheme': 'CUSTOM_XML', 'gtin': None, 'expiry_formatted': None, 'batch': None, 'serial': None,
                'extra': extra}

    # 3) Digits-only EAN/UPC (12/13/14)
    digits = re.sub(r'\D', '', p)
    if digits and len(digits) in (12, 13, 14):
        gt = normalize_gtin(digits)
        return {'scheme': 'EAN/UPC', 'gtin': gt, 'expiry_formatted': None, 'batch': None, 'serial': None,
                'extra': {}}

    # 4) GS1-like: contains GS separator or AI patterns
    if '\x1D' in p or '|GS|' in p or re.search(r'\(01\)', p) or re.search(r'01\d{14}', p):
        parsed = parse_gs1_data(p)
        return {'scheme': 'GS1',
                'gtin': parsed.get('gtin'),
                'expiry_formatted': parsed.get('expiry_formatted'),
                'batch': parsed.get('batch'),
                'serial': parsed.get('serial'),
                'extra': {}}

    # Default: RAW text
    return {'scheme': 'RAW', 'gtin': None, 'expiry_formatted': None, 'batch': None, 'serial': None,
            'extra': {'raw': p}}


# --- Decoder function (keeps your original approach) ---
def try_decode(frame):
    # use grayscale for zbar (tends to be more robust)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    r = zbar_decode(gray)
    if r:
        try:
            return r[0].data.decode('utf-8', errors='ignore')
        except:
            return str(r[0].data)
    # fallback: OpenCV QR detector (useful for some QR types)
    qrd = cv2.QRCodeDetector()
    data, pts, _ = qrd.detectAndDecode(frame)
    if data:
        return data
    return None


# --- Main loop (camera) ---
def main():
    cap = None
    # try several indices/backends; keep your original discovery approach
    for idx in [0, 1, 2]:
        for backend in [cv2.CAP_DSHOW, None]:
            try:
                cap = cv2.VideoCapture(idx, backend) if backend else cv2.VideoCapture(idx)
                if cap.isOpened():
                    print("Using camera index", idx, "backend", backend)
                    break
                else:
                    cap.release()
            except Exception:
                pass
        if cap and cap.isOpened():
            break
    if not cap or not cap.isOpened():
        print("camera open failed; try different index or CAP_DSHOW")
        sys.exit(1)

    print("Scanner started. Press 'q' to quit.")
    last_info = None
    last_rect = None

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        payload = try_decode(frame)
        if payload:
            # show raw payload repr for debugging hidden chars
            print("DETECTED payload (repr):", repr(payload))

            info = interpret_payload(payload)

            # map to the requested parsed_output structure
            parsed_output = {
                'scheme': info.get('scheme'),
                'gtin': info.get('gtin'),
                'expiry': info.get('expiry_formatted'),
                'batch': info.get('batch'),
                'serial': info.get('serial'),
                'status': check_validity(info.get('expiry_formatted') or None),
                'extra': info.get('extra', {})
            }

            print("PARSED ->", parsed_output)
            last_info = parsed_output
            # try to set rectangle area (we only have generic rectangle fallback here)
            try:
                # if pyzbar returned an object we could get rect; we don't have it here,
                # so use center box
                h, w = frame.shape[:2]
                last_rect = (int(w * 0.25), int(h * 0.25), int(w * 0.5), int(h * 0.5))
            except Exception:
                last_rect = None

        # overlay
        display = frame.copy()
        if last_info:
            # draw bounding box
            if last_rect:
                x, y, w, h = last_rect
                cv2.rectangle(display, (x, y), (x + w, y + h), (0, 255, 0), 2)
            # display parsed lines
            lines = [
                f"Scheme: {last_info.get('scheme')}",
                f"Status: {last_info.get('status')}",
                f"GTIN: {last_info.get('gtin')}",
                f"Expiry: {last_info.get('expiry')}",
                f"Batch: {last_info.get('batch')}",
                f"Serial: {last_info.get('serial')}"
            ]
            color = (0, 255, 0) if last_info.get('status') == 'VALID' else (0, 0, 255) if last_info.get('status') == 'EXPIRED' else (0, 165, 255)
            for i, ln in enumerate(lines):
                cv2.putText(display, ln, (10, 30 + 28 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            # If extra contains useful fields (URL or XML fields), show one-line hint
            extra = last_info.get('extra') or {}
            if extra:
                ex_preview = ""
                if 'url' in extra:
                    ex_preview = f"URL -> {extra['url']}"
                elif 'raw' in extra:
                    ex_preview = f"RAW -> {str(extra['raw'])[:60]}"
                else:
                    # show up to two xml fields if present
                    kvs = list(extra.items())[:2]
                    ex_preview = " | ".join(f"{k}:{v}" for k, v in kvs)
                cv2.putText(display, ex_preview, (10, display.shape[0] - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 2)

        cv2.imshow("Medicine Scanner", display)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()



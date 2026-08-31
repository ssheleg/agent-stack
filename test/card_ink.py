#!/usr/bin/env python3
"""Does the social card's text fit on the social card? Measured from its pixels.

Why this file exists at all
---------------------------
`test/social_preview.py` checked the PNG signature, the chunk order, the byte
count and the dimensions of `docs/assets/social-preview.png` — and never once
looked at the text printed on it. On 2026-08-31 every one of those checks was
green while the card's eyebrow ran off the right edge of the canvas and lost its
last eleven characters: the line read "…AND THE WALLET UNDER" and " LLM RESALE"
was never drawn. Measured on the committed file, accent ink painted to x=1199 of
a 1200-pixel canvas (board row B-118).

That is the whole class of defect this family refuses everywhere else — a claim
that fails without saying so — sitting on the single widest-read artefact the
pack publishes, the image every link preview renders. Bytes are not text, and a
sensor that counts bytes is not evidence about text.

Why it is a SEPARATE module and must stay one
---------------------------------------------
`test/social_preview.py` is a shared mechanism: nine repositories in this family
carry the same file, and the umbrella's `check_a_copied_mechanism_declares_its_
divergence` only compares copies that are at least 90% similar to each other.
Below that floor it treats the name as a coincidence and stops checking — for
ALL nine copies, because the comparison is against one base. Inlining this
decoder there would push the file past that floor and silently disable the
umbrella's guard on eight repositories that never asked for it. So the shared
file gains two lines and the machinery lives here. Do not merge this back in.

What is actually asserted
-------------------------
The renderer lives in the umbrella (`scripts/og-card.js`) and cannot be imported
from this repository, so the layout contract is restated here rather than
shared:

  * the canvas is 1200x630, and the content box is inset by PAD=84 on each side,
    so every painted glyph belongs to x in [84, 1116);
  * a 3px frame in the border colour runs around the whole canvas;
  * exactly one element bleeds out of the content box on purpose — the accent
    bar at the top-left corner, x 0..189, y 0..5.

So any pixel in the left or right gutter that is not the background, not the
frame and not that bar is text the renderer pushed out of the box. Clipping is
strictly worse than overflow and cannot hide behind this rule: the renderer's
smallest scale advances 14px per character, so a line long enough to lose even
one glyph has already painted past x=1186 — seventy pixels into the right
gutter — before the first character goes missing.

The positive assertion matters as much as the negative one. A blank or
mis-decoded image has no ink in the gutters either, and would sail through a
check that only looks for what must not be there; so the accent bar is required
to be present and whole, which is also the cheapest proof that the decoder
decoded and that the layout is the one these numbers describe.

Run it directly (`python3 test/card_ink.py --self-test`) to watch the guard
refuse a card that clips, and accept one that does not — synthesised in memory,
no fixture file to drift.
"""

from __future__ import annotations

import struct
import sys
import zlib

WIDTH = 1200
HEIGHT = 630
PAD = 84

# scripts/og-card.js PALETTE — the workbench dark twin.
BG = (0x0F, 0x12, 0x18)
LINE = (0x23, 0x2A, 0x36)
ACCENT = (0x4B, 0x8B, 0xFF)

# The one deliberate bleed: c.fill(0, 0, 190, 6, PALETTE.accent).
BAR_W = 190
BAR_H = 6

NAMED = {
    BG: "background",
    LINE: "frame",
    ACCENT: "accent",
    (0xE8, 0xEC, 0xF3): "ink (title/header)",
    (0x8A, 0x93, 0xA6): "muted (body line)",
    (0x5F, 0x68, 0x79): "dim (footer)",
}


def decode_rgb(data: bytes) -> tuple[int, int, bytes]:
    """Minimal PNG reader for the one shape this card is: 8-bit truecolour.

    Deliberately not Pillow. The card is generated with no dependencies and the
    check on it ships in a repository that installs none, so a decoder that
    covers exactly the encoder's output is the honest amount of machinery.
    """
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit("card_ink: not a PNG")
    idat = bytearray()
    width = height = depth = colour = None
    i = 8
    while i + 8 <= len(data):
        (length,) = struct.unpack(">I", data[i:i + 4])
        kind = data[i + 4:i + 8]
        body = data[i + 8:i + 8 + length]
        if kind == b"IHDR":
            width, height, depth, colour = struct.unpack(">IIBB", body[:10])
        elif kind == b"IDAT":
            idat += body
        elif kind == b"IEND":
            break
        i += 12 + length
    if width is None:
        raise SystemExit("card_ink: no IHDR")
    if (depth, colour) != (8, 2):
        raise SystemExit(
            f"card_ink: bit depth {depth}, colour type {colour} — this check reads "
            "8-bit truecolour, which is what scripts/og-card.js writes")
    raw = zlib.decompress(bytes(idat))
    stride = width * 3
    out = bytearray(height * stride)
    prev = bytes(stride)
    pos = 0
    for y in range(height):
        filt = raw[pos]
        pos += 1
        row = bytearray(raw[pos:pos + stride])
        pos += stride
        if filt == 1:
            for x in range(3, stride):
                row[x] = (row[x] + row[x - 3]) & 0xFF
        elif filt == 2:
            for x in range(stride):
                row[x] = (row[x] + prev[x]) & 0xFF
        elif filt == 3:
            for x in range(stride):
                left = row[x - 3] if x >= 3 else 0
                row[x] = (row[x] + ((left + prev[x]) >> 1)) & 0xFF
        elif filt == 4:
            for x in range(stride):
                a = row[x - 3] if x >= 3 else 0
                b = prev[x]
                c = prev[x - 3] if x >= 3 else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                row[x] = (row[x] + (a if pa <= pb and pa <= pc
                                    else b if pb <= pc else c)) & 0xFF
        elif filt != 0:
            raise SystemExit(f"card_ink: unknown row filter {filt}")
        out[y * stride:(y + 1) * stride] = row
        prev = bytes(row)
    return width, height, bytes(out)


def _allowed(x: int, y: int, px: tuple[int, int, int]) -> bool:
    if px in (BG, LINE):
        return True
    return px == ACCENT and x < BAR_W and y < BAR_H


def ink_stays_in_the_content_box(path, data: bytes, width: int, height: int) -> None:
    """Refuse a card whose text left the content box — clipped or merely spilled.

    `path`, `width` and `height` come from the caller so the message names the
    file the caller was checking and the two readings agree by construction
    rather than by a second decode.
    """
    w, h, px = decode_rgb(data)
    if (w, h) != (width, height):
        raise SystemExit(
            f"{path}: IHDR says {width}x{height} and the decoded image is {w}x{h}")
    if (w, h) != (WIDTH, HEIGHT):
        raise SystemExit(
            f"{path}: {w}x{h} — this check knows the {WIDTH}x{HEIGHT} layout only")

    box_l, box_r = PAD, w - PAD           # content box: [84, 1116)
    gutters = list(range(0, box_l)) + list(range(box_r, w))

    seen_bar = 0
    worst = None                          # (distance past the box, x, y, colour)
    for y in range(h):
        base = y * w * 3
        for x in gutters:
            o = base + x * 3
            c = (px[o], px[o + 1], px[o + 2])
            if x < BAR_W and y < BAR_H and c == ACCENT:
                seen_bar += 1
                continue
            if _allowed(x, y, c):
                continue
            past = (box_l - x) if x < box_l else (x - box_r + 1)
            if worst is None or past > worst[0]:
                worst = (past, x, y, c)

    if worst is not None:
        past, x, y, c = worst
        side = "left" if x < box_l else "right"
        edge = box_l if x < box_l else box_r - 1
        clipped = x >= w - 3
        raise SystemExit(
            f"{path}: {NAMED.get(c, 'unknown ' + repr(c))} paints at x={x}, y={y} — "
            f"{past}px past the {side} edge of the content box (x={edge})"
            + (", and reaches the canvas edge, so characters were cut off entirely"
               if clipped else "")
            + ". The renderer floors at its smallest scale, so no scale fixes this: "
              "shorten the text the card is generated from (the `role` cell in the "
              "umbrella's skills.json feeds the eyebrow), regenerate the card, and "
              "recommit it.")

    # Only the first PAD columns of the 190px bar lie in the scanned gutter; the
    # rest of it is inside the content box, where this check does not look.
    expected_bar = PAD * BAR_H
    if seen_bar != expected_bar:
        raise SystemExit(
            f"{path}: the accent bar covers {seen_bar} of the {expected_bar} left-gutter "
            "pixels it is drawn on. "
            "Either the layout this check describes is no longer the layout being "
            "rendered, or the image did not decode — and an all-clear from a check "
            "that found no card is worth nothing. Re-read this file's contract "
            "against scripts/og-card.js in the umbrella.")


# ------------------------------------------------------------------ self-test

def encode_rgb(pixels: bytes, w: int = WIDTH, h: int = HEIGHT) -> bytes:
    def chunk(kind: bytes, body: bytes) -> bytes:
        return (struct.pack(">I", len(body)) + kind + body
                + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF))

    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += pixels[y * w * 3:(y + 1) * w * 3]
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def _synthetic(spill: int = 0) -> bytes:
    """A card-shaped image: frame, accent bar, and `spill` px of ink past the box."""
    px = bytearray(bytes(BG) * (WIDTH * HEIGHT))

    def put(x, y, colour):
        o = (y * WIDTH + x) * 3
        px[o:o + 3] = bytes(colour)

    for y in range(HEIGHT):
        for x in range(WIDTH):
            if x < 3 or x >= WIDTH - 3 or y < 3 or y >= HEIGHT - 3:
                put(x, y, LINE)
    for y in range(BAR_H):
        for x in range(BAR_W):
            put(x, y, ACCENT)
    for x in range(PAD, PAD + 400):       # legitimate ink, inside the box
        put(x, 300, (0xE8, 0xEC, 0xF3))
    for x in range(WIDTH - PAD, WIDTH - PAD + spill):
        put(x, 200, ACCENT)               # the eyebrow, running out of the box
    return encode_rgb(bytes(px))


def self_test() -> None:
    clean = _synthetic(0)
    ink_stays_in_the_content_box("<synthetic clean>", clean, WIDTH, HEIGHT)
    print("OK: a card whose ink stays in the content box passes")

    for spill, label in ((1, "one pixel past the box"),
                         (PAD, "ink to the canvas edge, characters lost")):
        try:
            ink_stays_in_the_content_box("<synthetic spill>", _synthetic(spill),
                                         WIDTH, HEIGHT)
        except SystemExit as exc:
            print(f"OK: refused — {label}: {str(exc)[:96]}...")
        else:
            raise SystemExit(
                f"card_ink self-test: ink {spill}px past the content box was accepted; "
                "the guard is asleep and every card it clears is unmeasured")

    blank = encode_rgb(bytes(bytes(BG) * (WIDTH * HEIGHT)))
    try:
        ink_stays_in_the_content_box("<synthetic blank>", blank, WIDTH, HEIGHT)
    except SystemExit as exc:
        print(f"OK: refused — a blank image cannot pass by having no ink: "
              f"{str(exc)[:72]}...")
    else:
        raise SystemExit(
            "card_ink self-test: a blank image passed; the check clears anything "
            "with nothing in the gutters, which is the emptiest kind of green")


if __name__ == "__main__":
    if "--self-test" in sys.argv[1:]:
        self_test()
    else:
        raise SystemExit("usage: python3 test/card_ink.py --self-test "
                         "(the card itself is checked by test/social_preview.py)")

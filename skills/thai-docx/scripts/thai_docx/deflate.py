# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""A deflate of this project's own, so that both implementations compress to the same bytes.

`repair` rewrites parts of a package a user handed over, and ADR 0008 says the two
implementations must write the same bytes. No two compression libraries promise that — zlib's
output depends on its version, its level and its strategy — so a repaired part was stored
uncompressed, and a document with a large styles part came back ten times its size
(`docs/evidence/2026-09-18-repair-marks-thai-and-fills-the-twins.md`).

This module compresses. It is not fast and it is not the smallest: it is **defined**, so that
Python and JavaScript agree by construction rather than by hoping two libraries do. Every
choice a compressor is free to make is fixed here:

1. One deflate stream of fixed-Huffman blocks (`BTYPE=01`, RFC 1951 §3.2.6). No dynamic
   trees: a dynamic tree is a second thing the two implementations would have to build
   identically, for a gain this project does not need.
2. Matches are found with a chained hash of three bytes, `HASH_BITS` wide, over a window of
   `WINDOW` bytes. The chain is walked from the most recent position back, at most
   `MAX_CHAIN` links; the longest match wins, and the nearest of equal length, because the
   walk stops improving only on a strictly longer one.
3. A match of at least `MIN_MATCH` and at most `MAX_MATCH` bytes is taken as soon as it is
   found: greedy, never lazy. Every position the match covers is entered into the chain.
4. A block is closed after `BLOCK_BYTES` of input, and the last one carries `BFINAL`.

The result inflates with any reader — zlib, Word, this project's own `inflateRaw` — which the
tests check both ways.
"""

from __future__ import annotations

WINDOW = 32768
MIN_MATCH, MAX_MATCH = 3, 258
HASH_BITS = 15
MAX_CHAIN = 128
BLOCK_BYTES = 1 << 16

# RFC 1951 §3.2.5: the length and distance codes, and their extra bits.
LEN_BASE = (3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 23, 27, 31, 35, 43, 51, 59,
            67, 83, 99, 115, 131, 163, 195, 227, 258)
LEN_EXTRA = (0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 0)
DIST_BASE = (1, 2, 3, 4, 5, 7, 9, 13, 17, 25, 33, 49, 65, 97, 129, 193, 257, 385, 513, 769,
             1025, 1537, 2049, 3073, 4097, 6145, 8193, 12289, 16385, 24577)
DIST_EXTRA = (0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13)


class _Bits:
    """Deflate's bit order: bits fill a byte from its least significant end, and a Huffman
    code is written from its most significant bit (RFC 1951 §3.1.1)."""

    def __init__(self) -> None:
        self.out = bytearray()
        self.bit = 0
        self.acc = 0

    def put(self, value: int, count: int) -> None:
        self.acc |= (value & ((1 << count) - 1)) << self.bit
        self.bit += count
        while self.bit >= 8:
            self.out.append(self.acc & 0xFF)
            self.acc >>= 8
            self.bit -= 8

    def put_code(self, code: int, count: int) -> None:
        for i in range(count - 1, -1, -1):
            self.put((code >> i) & 1, 1)

    def finish(self) -> bytes:
        if self.bit:
            self.out.append(self.acc & 0xFF)
        return bytes(self.out)


def _literal(bits: _Bits, value: int) -> None:
    """The fixed literal/length code of RFC 1951 §3.2.6."""
    if value < 144:
        bits.put_code(0b00110000 + value, 8)
    elif value < 256:
        bits.put_code(0b110010000 + value - 144, 9)
    elif value < 280:
        bits.put_code(value - 256, 7)
    else:
        bits.put_code(0b11000000 + value - 280, 8)


def _length_code(length: int) -> int:
    for i in range(len(LEN_BASE) - 1, -1, -1):
        if length >= LEN_BASE[i]:
            return i
    raise ValueError("a match shorter than the shortest length code")


def _distance_code(distance: int) -> int:
    for i in range(len(DIST_BASE) - 1, -1, -1):
        if distance >= DIST_BASE[i]:
            return i
    raise ValueError("a match nearer than the nearest distance code")


def deflate(data: bytes) -> bytes:
    """`data` as a raw deflate stream — what a zip entry of method 8 carries."""
    bits = _Bits()
    size = len(data)
    head = [-1] * (1 << HASH_BITS)
    prev = [-1] * max(size, 1)
    i = 0
    block_start = 0
    # Every block of data carries BFINAL=0 and the stream is closed by an empty final block.
    # Ten bits, and the writer never has to know which block will turn out to be the last.
    if size:
        bits.put(0, 1)
        bits.put(1, 2)
    while i < size:
        if i - block_start >= BLOCK_BYTES:
            _literal(bits, 256)
            bits.put(0, 1)
            bits.put(1, 2)
            block_start = i
        best_len, best_dist = 0, 0
        longest = min(MAX_MATCH, size - i)  # a match never runs past the end of the input
        if longest >= MIN_MATCH:
            key = ((data[i] << 16) | (data[i + 1] << 8) | data[i + 2]) % (1 << HASH_BITS)
            at, steps = head[key], 0
            limit = i - WINDOW  # -1 ends the chain, and a negative limit must not let it pass
            while at >= 0 and at > limit and steps < MAX_CHAIN:
                steps += 1
                # the byte past the best match so far: if it differs, this one cannot win
                if data[at + best_len] == data[i + best_len]:
                    length = 0
                    while length < longest and data[at + length] == data[i + length]:
                        length += 1
                    if length > best_len:
                        best_len, best_dist = length, i - at
                        if best_len >= longest:
                            break
                at = prev[at]
        if best_len >= MIN_MATCH:
            code = _length_code(best_len)
            _literal(bits, 257 + code)
            bits.put(best_len - LEN_BASE[code], LEN_EXTRA[code])
            dcode = _distance_code(best_dist)
            bits.put_code(dcode, 5)
            bits.put(best_dist - DIST_BASE[dcode], DIST_EXTRA[dcode])
            taken = best_len
        else:
            _literal(bits, data[i])
            taken = 1
        for j in range(i, i + taken):
            if j + MIN_MATCH <= size:
                key = ((data[j] << 16) | (data[j + 1] << 8) | data[j + 2]) % (1 << HASH_BITS)
                prev[j] = head[key]
                head[key] = j
        i += taken
    if size:
        _literal(bits, 256)
    bits.put(1, 1)       # BFINAL
    bits.put(1, 2)       # BTYPE: fixed Huffman
    _literal(bits, 256)  # an empty block: nothing but its end
    return bits.finish()

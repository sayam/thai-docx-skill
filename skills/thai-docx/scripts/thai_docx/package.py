"""The .docx container: writing stored entries, and reading entries by the rules
ADR 0017 numbers — the same rules js/10-zip.js follows, so a damaged package gets
the same verdict from both implementations and from every Python release.
"""

from __future__ import annotations

import zlib
from typing import NamedTuple

MAX_FILE = 64 * 1024 * 1024
LIMIT_64 = 1 << 53
DOS_DATE = 33  # 1980-01-01
SIG_LOCAL, SIG_CENTRAL, SIG_END, SIG_END64, SIG_LOCATOR = 0x04034B50, 0x02014B50, 0x06054B50, 0x06064B50, 0x07064B50


class PackageError(Exception):
    pass


class Entry(NamedTuple):
    name: str
    name_bytes: bytes
    flags: int
    method: int
    crc: int
    compress_size: int
    file_size: int
    header_offset: int


def _u16(n: int) -> bytes:
    return n.to_bytes(2, "little")


def _u32(n: int) -> bytes:
    return n.to_bytes(4, "little")


def pack(parts: list[tuple[str, bytes]]) -> bytes:
    """Stored entries in the order given, fixed date, no extra fields (ADR 0017)."""
    out, central, offset = bytearray(), bytearray(), 0
    for name, data in parts:
        name_bytes = name.encode("utf-8")
        flags = 0 if name.isascii() else 0x800
        crc = zlib.crc32(data)
        fields = _u16(flags) + _u16(0) + _u16(0) + _u16(DOS_DATE) + _u32(crc) + _u32(len(data)) + _u32(len(data)) + _u16(len(name_bytes)) + _u16(0)
        local = _u32(SIG_LOCAL) + _u16(20) + fields
        out += local + name_bytes + data
        central += _u32(SIG_CENTRAL) + _u16(20) + _u16(20) + fields + _u16(0) + _u16(0) + _u16(0) + _u32(0o600 << 16) + _u32(offset) + name_bytes
        offset += len(local) + len(name_bytes) + len(data)
    end = _u32(SIG_END) + _u16(0) + _u16(0) + _u16(len(parts)) + _u16(len(parts)) + _u32(len(central)) + _u32(offset) + _u16(0)
    return bytes(out + central + end)


def _rd(b: bytes, o: int, n: int) -> int:
    if o < 0 or o + n > len(b):
        raise PackageError("read past the end")
    value = int.from_bytes(b[o : o + n], "little")
    if n == 8 and value >= LIMIT_64:
        raise PackageError("64-bit value too large")
    return value


def entries(b: bytes) -> list[Entry]:
    """The central directory (rules 2–5)."""
    size = len(b)
    if size < 22:
        raise PackageError("too short")
    end = -1
    if _rd(b, size - 22, 4) == SIG_END and _rd(b, size - 2, 2) == 0:
        end = size - 22
    else:
        for i in range(size - 22, max(0, size - 22 - 65535) - 1, -1):
            if b[i : i + 4] == b"PK\x05\x06" and i + 22 + _rd(b, i + 20, 2) == size:
                end = i
                break
    if end < 0:
        raise PackageError("no end record")
    count, cd_size, cd_offset, record = _rd(b, end + 10, 2), _rd(b, end + 12, 4), _rd(b, end + 16, 4), end
    if end >= 20 and _rd(b, end - 20, 4) == SIG_LOCATOR:
        record = end - 20 - 56
        if record < 0 or _rd(b, record, 4) != SIG_END64:
            raise PackageError("no zip64 end record")
        count, cd_size, cd_offset = _rd(b, record + 32, 8), _rd(b, record + 40, 8), _rd(b, record + 48, 8)
    concat = record - cd_size - cd_offset
    if concat < 0:
        raise PackageError("central directory overlaps its end record")
    found: list[Entry] = []
    p = cd_offset + concat
    while p < record:
        if p + 46 > record or _rd(b, p, 4) != SIG_CENTRAL:
            raise PackageError("bad central directory record")
        flags, method, crc = _rd(b, p + 8, 2), _rd(b, p + 10, 2), _rd(b, p + 16, 4)
        compress_size, file_size = _rd(b, p + 20, 4), _rd(b, p + 24, 4)
        name_len, extra_len, comment_len = _rd(b, p + 28, 2), _rd(b, p + 30, 2), _rd(b, p + 32, 2)
        header_offset = _rd(b, p + 42, 4)
        # a record that runs past the directory is refused below, where p passes record
        x, extra_end = p + 46 + name_len, p + 46 + name_len + extra_len
        name_bytes = b[p + 46 : x]
        try:
            name = name_bytes.decode("utf-8") if flags & 0x800 else name_bytes.decode("cp437")
        except UnicodeDecodeError:
            raise PackageError("name is not UTF-8") from None
        while x + 4 <= extra_end:
            field_id, field_len = _rd(b, x, 2), _rd(b, x + 2, 2)
            if x + 4 + field_len > extra_end:
                raise PackageError("extra field runs past its entry")
            if field_id == 1:
                q = x + 4
                if file_size == 0xFFFFFFFF:
                    if q + 8 > x + 4 + field_len:
                        raise PackageError("zip64 field too short")
                    file_size, q = _rd(b, q, 8), q + 8
                if compress_size == 0xFFFFFFFF:
                    if q + 8 > x + 4 + field_len:
                        raise PackageError("zip64 field too short")
                    compress_size, q = _rd(b, q, 8), q + 8
                if header_offset == 0xFFFFFFFF:
                    if q + 8 > x + 4 + field_len:
                        raise PackageError("zip64 field too short")
                    header_offset, q = _rd(b, q, 8), q + 8
            x += 4 + field_len
        found.append(Entry(name, name_bytes, flags, method, crc, compress_size, file_size, header_offset + concat))
        p = extra_end + comment_len
    if p != record or len(found) != count:
        raise PackageError("central directory does not add up")
    return found


def read(b: bytes, e: Entry) -> bytes:
    """One entry's bytes (rules 8–10)."""
    h = e.header_offset
    if _rd(b, h, 4) != SIG_LOCAL:
        raise PackageError("bad local header")
    name_len, extra_len = _rd(b, h + 26, 2), _rd(b, h + 28, 2)
    start = h + 30 + name_len + extra_len
    if start > len(b) or b[h + 30 : h + 30 + name_len] != e.name_bytes:
        raise PackageError("local name differs")
    if start + e.compress_size > len(b):
        raise PackageError("entry runs past the end")
    raw = b[start : start + e.compress_size]
    if e.method == 0:
        if e.compress_size != e.file_size:
            raise PackageError("stored sizes differ")
        data = raw
    else:
        inflater = zlib.decompressobj(-15)
        try:
            data = inflater.decompress(raw, e.file_size + 1)
        except zlib.error:
            raise PackageError("bad deflate data") from None
        if not inflater.eof or len(data) != e.file_size:
            raise PackageError("deflate data does not give the declared size")
    if zlib.crc32(data) != e.crc:
        raise PackageError("bad checksum")
    return data

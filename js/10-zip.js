// SPDX-FileCopyrightText: 2026 Sayam Sriphua
// SPDX-License-Identifier: MIT
// thai-docx — zip: writing stored entries, repacking with rewritten parts deflated (repair),
// and reading stored or deflated entries
// by the rules ADR 0017 numbers, as thai_docx/package.py does (ADR 0008, 0040 §9).

class ZipError extends Error {}

function u16(n) {
  return [n & 0xff, (n >>> 8) & 0xff];
}

function u32(n) {
  return [n & 0xff, (n >>> 8) & 0xff, (n >>> 16) & 0xff, (n >>> 24) & 0xff];
}

// parts: [[name, Uint8Array], ...] — stored, 1980-01-01 00:00:00, attributes 0o600.
function packZip(parts) {
  const chunks = [];
  const central = [];
  let offset = 0;
  const DOS_DATE = 33; // (1980 - 1980) << 9 | 1 << 5 | 1
  for (const [name, data] of parts) {
    const nameBytes = utf8(name);
    let ascii = true;
    for (const b of nameBytes) if (b > 0x7f) ascii = false;
    const flags = ascii ? 0 : 0x800;
    const crc = crc32(data);
    const local = new Uint8Array([
      ...u32(0x04034b50), ...u16(20), ...u16(flags), ...u16(0), ...u16(0), ...u16(DOS_DATE),
      ...u32(crc), ...u32(data.length), ...u32(data.length), ...u16(nameBytes.length), ...u16(0),
    ]);
    chunks.push(local, nameBytes, data);
    central.push(new Uint8Array([
      ...u32(0x02014b50), ...u16(20), ...u16(20), ...u16(flags), ...u16(0), ...u16(0), ...u16(DOS_DATE),
      ...u32(crc), ...u32(data.length), ...u32(data.length), ...u16(nameBytes.length), ...u16(0), ...u16(0),
      ...u16(0), ...u16(0), ...u32(0o600 << 16), ...u32(offset),
    ]), nameBytes);
    offset += local.length + nameBytes.length + data.length;
  }
  let cdSize = 0;
  for (const c of central) cdSize += c.length;
  const eocd = new Uint8Array([
    ...u32(0x06054b50), ...u16(0), ...u16(0), ...u16(parts.length), ...u16(parts.length),
    ...u32(cdSize), ...u32(offset), ...u16(0),
  ]);
  return concatBytes([...chunks, ...central, eocd]);
}

// The package again, in the order it had: an entry named in `replace` is written anew, every
// other entry keeps the bytes it already had — its method, its checksum, its sizes and its
// date (ADR 0037). A rewritten entry is compressed by this project's own deflate, which both
// implementations run to the same bytes by construction (ADR 0008).
function repackZip(b, ents, replace) {
  const names = new Set(ents.map((e) => e.name));
  for (const name of Object.keys(replace)) {
    // a name that is not in the package would leave the file unchanged, quietly
    if (!names.has(name)) throw new ZipError("the package has no entry named '" + name + "'");
  }
  const chunks = [];
  const central = [];
  let offset = 0;
  for (const e of ents) {
    const replacing = Object.prototype.hasOwnProperty.call(replace, e.name);
    const fresh = replacing ? replace[e.name] : null;
    // a rewritten entry is compressed by this project's own deflate, which both
    // implementations run to the same bytes; stored when compressing would make it larger
    const packed = replacing ? deflate(fresh) : null;
    const smaller = replacing && packed.length < fresh.length;
    const payload = replacing ? (smaller ? packed : fresh) : rawZipEntry(b, e);
    const flags = e.flags & 0x800;
    const method = replacing ? (smaller ? 8 : 0) : e.method;
    const crc = replacing ? crc32(fresh) : e.crc;
    const csize = replacing ? payload.length : e.compressSize;
    const usize = replacing ? fresh.length : e.fileSize;
    const fields = [...u16(flags), ...u16(method), ...u32(e.mod), ...u32(crc),
      ...u32(csize), ...u32(usize), ...u16(e.nameBytes.length), ...u16(0)];
    const local = new Uint8Array([...u32(SIG_LOCAL), ...u16(20), ...fields]);
    chunks.push(local, e.nameBytes, payload);
    central.push(new Uint8Array([
      ...u32(SIG_CENTRAL), ...u16(e.madeBy), ...u16(20), ...fields,
      ...u16(0), ...u16(0), ...u16(0), ...u32(e.attrs), ...u32(offset),
    ]), e.nameBytes);
    offset += local.length + e.nameBytes.length + payload.length;
  }
  let cdSize = 0;
  for (const c of central) cdSize += c.length;
  const eocd = new Uint8Array([
    ...u32(SIG_END), ...u16(0), ...u16(0), ...u16(ents.length), ...u16(ents.length),
    ...u32(cdSize), ...u32(offset), ...u16(0),
  ]);
  return concatBytes([...chunks, ...central, eocd]);
}

// One entry's bytes **as the package holds them** — still compressed, if it is.
function rawZipEntry(b, e) {
  const h = e.headerOffset;
  if (rd(b, h, 4) !== SIG_LOCAL) throw new ZipError("bad local header");
  const start = h + 30 + rd(b, h + 26, 2) + rd(b, h + 28, 2);
  if (start + e.compressSize > b.length) throw new ZipError("entry runs past the end");
  return b.subarray(start, start + e.compressSize);
}

// --- reading ------------------------------------------------------------------------

// cp437, for entry names written without the UTF-8 flag (as zipfile decodes them)
const CP437_HIGH =
  "ÇüéâäàåçêëèïîìÄÅÉæÆôöòûùÿÖÜ¢£¥₧ƒáíóúñÑªº¿⌐¬½¼¡«»░▒▓│┤╡╢╖╕╣║╗╝╜╛┐└┴┬├─┼╞╟╚╔╩╦╠═╬╧╨╤╥╙╘╒╓╫╪┘┌█▄▌▐▀αßΓπΣσµτΦΘΩδ∞φε∩≡±≥≤⌠⌡÷≈°∙·√ⁿ²■ ";

function decodeName(bytes, utf8Flag) {
  if (utf8Flag) {
    const s = fromUtf8(bytes);
    if (s === null) throw new ZipError("bad name");
    return s;
  }
  let s = "";
  for (const b of bytes) s += b < 0x80 ? String.fromCharCode(b) : CP437_HIGH[b - 0x80];
  return s;
}

// Every read is bounds-checked; a 64-bit value must stay below 2^53 (ADR 0017 §3).
function rd(b, o, n) {
  if (o < 0 || o + n > b.length) throw new ZipError("read past the end");
  if (n === 2) return b[o] | (b[o + 1] << 8);
  if (n === 4) return (b[o] | (b[o + 1] << 8) | (b[o + 2] << 16) | (b[o + 3] << 24)) >>> 0;
  const high = rd(b, o + 4, 4);
  if (high >= 0x200000) throw new ZipError("64-bit value too large");
  return rd(b, o, 4) + high * 0x100000000;
}

const SIG_LOCAL = 0x04034b50, SIG_CENTRAL = 0x02014b50, SIG_END = 0x06054b50, SIG_END64 = 0x06064b50, SIG_LOCATOR = 0x07064b50;

// The central directory, by ADR 0017 rules 2–5.
function readZipDirectory(b) {
  const size = b.length;
  if (size < 22) throw new ZipError("too short");
  let end = -1;
  if (rd(b, size - 22, 4) === SIG_END && rd(b, size - 2, 2) === 0) {
    end = size - 22;
  } else {
    const floor = Math.max(0, size - 22 - 65535);
    for (let i = size - 22; i >= floor; i--) {
      if (b[i] === 0x50 && b[i + 1] === 0x4b && b[i + 2] === 5 && b[i + 3] === 6 && i + 22 + rd(b, i + 20, 2) === size) {
        end = i;
        break;
      }
    }
  }
  if (end < 0) throw new ZipError("no end record");
  let count = rd(b, end + 10, 2), cdSize = rd(b, end + 12, 4), cdOffset = rd(b, end + 16, 4), record = end;
  if (end >= 20 && rd(b, end - 20, 4) === SIG_LOCATOR) {
    record = end - 20 - 56;
    if (record < 0 || rd(b, record, 4) !== SIG_END64) throw new ZipError("no zip64 end record");
    count = rd(b, record + 32, 8);
    cdSize = rd(b, record + 40, 8);
    cdOffset = rd(b, record + 48, 8);
  }
  const concat = record - cdSize - cdOffset;
  if (concat < 0) throw new ZipError("central directory overlaps its end record");
  const entries = [];
  let p = cdOffset + concat;
  while (p < record) {
    if (p + 46 > record || rd(b, p, 4) !== SIG_CENTRAL) throw new ZipError("bad central directory record");
    const flags = rd(b, p + 8, 2), method = rd(b, p + 10, 2), crc = rd(b, p + 16, 4);
    const mod = rd(b, p + 12, 4), madeBy = rd(b, p + 4, 2), attrs = rd(b, p + 38, 4);
    let compressSize = rd(b, p + 20, 4), fileSize = rd(b, p + 24, 4);
    const nameLen = rd(b, p + 28, 2), extraLen = rd(b, p + 30, 2), commentLen = rd(b, p + 32, 2);
    let headerOffset = rd(b, p + 42, 4);
    let x = p + 46 + nameLen;
    // a record that runs past the directory is refused below, where p passes record
    const extraEnd = x + extraLen;
    const nameBytes = b.subarray(p + 46, x);
    const name = decodeName(nameBytes, (flags & 0x800) !== 0);
    while (x + 4 <= extraEnd) {
      const id = rd(b, x, 2), len = rd(b, x + 2, 2);
      const fieldEnd = x + 4 + len;
      if (fieldEnd > extraEnd) throw new ZipError("extra field runs past its entry");
      if (id === 1) {
        let q = x + 4;
        const take = () => {
          if (q + 8 > fieldEnd) throw new ZipError("zip64 field too short");
          const v = rd(b, q, 8);
          q += 8;
          return v;
        };
        if (fileSize === 0xffffffff) fileSize = take();
        if (compressSize === 0xffffffff) compressSize = take();
        if (headerOffset === 0xffffffff) headerOffset = take();
      }
      x = fieldEnd;
    }
    entries.push({ name, nameBytes, flags, method, crc, compressSize, fileSize, headerOffset: headerOffset + concat, mod, madeBy, attrs });
    p = extraEnd + commentLen;
  }
  if (p !== record || entries.length !== count) throw new ZipError("central directory does not add up");
  return entries;
}

// One entry's bytes, by ADR 0017 rules 8–10.
function readZipEntry(b, e) {
  const h = e.headerOffset;
  if (rd(b, h, 4) !== SIG_LOCAL) throw new ZipError("bad local header");
  const nameLen = rd(b, h + 26, 2), extraLen = rd(b, h + 28, 2);
  const start = h + 30 + nameLen + extraLen;
  if (start > b.length) throw new ZipError("local name differs");
  for (let i = 0; i < nameLen; i++) if (b[h + 30 + i] !== e.nameBytes[i]) throw new ZipError("local name differs");
  if (nameLen !== e.nameBytes.length) throw new ZipError("local name differs");
  if (start + e.compressSize > b.length) throw new ZipError("entry runs past the end");
  const raw = b.subarray(start, start + e.compressSize);
  let data;
  if (e.method === 0) {
    if (e.compressSize !== e.fileSize) throw new ZipError("stored sizes differ");
    data = raw;
  } else {
    data = inflateRaw(raw, e.fileSize);
  }
  if (crc32(data) !== e.crc) throw new ZipError("bad checksum");
  return data;
}

// --- inflate (RFC 1951), bounded by the size the directory declares ------------------

const LEN_BASE = [3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 23, 27, 31, 35, 43, 51, 59, 67, 83, 99, 115, 131, 163, 195, 227, 258];
const LEN_EXTRA = [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 0];
const DIST_BASE = [1, 2, 3, 4, 5, 7, 9, 13, 17, 25, 33, 49, 65, 97, 129, 193, 257, 385, 513, 769, 1025, 1537, 2049, 3073, 4097, 6145, 8193, 12289, 16385, 24577];
const DIST_EXTRA = [0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13];
const CL_ORDER = [16, 17, 18, 0, 8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 13, 2, 14, 1, 15];

// A canonical Huffman code. As zlib's inflate_table: an over-subscribed set is
// refused, and so is an incomplete one — except that a literal/length or distance
// code may be a single one-bit code, and any code may be empty (`codeLengths`
// marks the code-length code, which gets no exception but the empty one).
function huffman(lengths, codeLengths) {
  const counts = new Uint16Array(16);
  for (const l of lengths) counts[l]++;
  counts[0] = 0;
  let max = 0;
  for (let len = 1; len < 16; len++) if (counts[len]) max = len;
  let left = 1;
  for (let len = 1; len < 16; len++) {
    left = left * 2 - counts[len];
    if (left < 0) throw new ZipError("over-subscribed code");
  }
  if (max > 0 && left > 0 && (codeLengths || max !== 1)) throw new ZipError("incomplete code");
  const offs = new Uint16Array(16);
  for (let i = 1; i < 16; i++) offs[i] = offs[i - 1] + counts[i - 1];
  const symbols = new Uint16Array(lengths.length);
  for (let s = 0; s < lengths.length; s++) if (lengths[s]) symbols[offs[lengths[s]]++] = s;
  return { counts, symbols };
}

function inflateRaw(input, expected) {
  const out = new Uint8Array(expected);
  let op = 0;
  let ip = 0;
  let bitbuf = 0;
  let bitcnt = 0;
  const bits = (n) => {
    while (bitcnt < n) {
      if (ip >= input.length) throw new ZipError("truncated deflate");
      bitbuf |= input[ip++] << bitcnt;
      bitcnt += 8;
    }
    const v = bitbuf & ((1 << n) - 1);
    bitbuf >>>= n;
    bitcnt -= n;
    return v;
  };
  const decode = (h) => {
    let code = 0, first = 0, index = 0;
    for (let len = 1; len < 16; len++) {
      code |= bits(1);
      const count = h.counts[len];
      if (code - count < first) return h.symbols[index + (code - first)];
      index += count;
      first += count;
      first <<= 1;
      code <<= 1;
    }
    throw new ZipError("bad huffman code");
  };
  const put = (v) => {
    if (op >= expected) throw new ZipError("inflates past its declared size");
    out[op++] = v;
  };
  let fixedLit = null, fixedDist = null;
  let last = 0;
  while (!last) {
    last = bits(1);
    const type = bits(2);
    if (type === 0) {
      bitbuf = 0;
      bitcnt = 0;
      if (ip + 4 > input.length) throw new ZipError("truncated stored block");
      const len = input[ip] | (input[ip + 1] << 8);
      const nlen = input[ip + 2] | (input[ip + 3] << 8);
      ip += 4;
      if (len !== (~nlen & 0xffff)) throw new ZipError("bad stored block");
      if (ip + len > input.length) throw new ZipError("truncated stored block");
      for (let i = 0; i < len; i++) put(input[ip++]);
    } else if (type === 1 || type === 2) {
      let lit, dist;
      if (type === 1) {
        if (fixedLit === null) {
          const l = new Uint8Array(288);
          for (let i = 0; i < 144; i++) l[i] = 8;
          for (let i = 144; i < 256; i++) l[i] = 9;
          for (let i = 256; i < 280; i++) l[i] = 7;
          for (let i = 280; i < 288; i++) l[i] = 8;
          fixedLit = huffman(l, false);
          fixedDist = huffman(new Uint8Array(32).fill(5), false);
        }
        lit = fixedLit;
        dist = fixedDist;
      } else {
        const hlit = bits(5) + 257, hdist = bits(5) + 1, hclen = bits(4) + 4;
        if (hlit > 286 || hdist > 30) throw new ZipError("bad dynamic header");
        const cl = new Uint8Array(19);
        for (let i = 0; i < hclen; i++) cl[CL_ORDER[i]] = bits(3);
        const clh = huffman(cl, true);
        const lengths = new Uint8Array(hlit + hdist);
        let i = 0;
        while (i < hlit + hdist) {
          const sym = decode(clh);
          if (sym < 16) lengths[i++] = sym;
          else {
            let rep, val = 0;
            if (sym === 16) {
              if (i === 0) throw new ZipError("repeat with no length");
              val = lengths[i - 1];
              rep = 3 + bits(2);
            } else if (sym === 17) rep = 3 + bits(3);
            else rep = 11 + bits(7);
            if (i + rep > hlit + hdist) throw new ZipError("too many lengths");
            while (rep--) lengths[i++] = val;
          }
        }
        if (lengths[256] === 0) throw new ZipError("no end of block code");
        lit = huffman(lengths.subarray(0, hlit), false);
        dist = huffman(lengths.subarray(hlit), false);
      }
      for (;;) {
        let sym = decode(lit);
        if (sym < 256) put(sym);
        else if (sym === 256) break;
        else {
          sym -= 257;
          if (sym >= 29) throw new ZipError("bad length symbol");
          const len = LEN_BASE[sym] + bits(LEN_EXTRA[sym]);
          const ds = decode(dist);
          if (ds >= 30) throw new ZipError("bad distance symbol");
          const d = DIST_BASE[ds] + bits(DIST_EXTRA[ds]);
          if (d > op) throw new ZipError("distance too far back");
          for (let k = 0; k < len; k++) put(out[op - d]);
        }
      }
    } else {
      throw new ZipError("bad block type");
    }
  }
  if (op !== expected) throw new ZipError("deflate data does not give the declared size");
  return out;
}

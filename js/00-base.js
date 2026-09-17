// thai-docx — base: text, hashing, and Python's JSON, spelled out so that this
// JavaScript implementation prints what the Python one prints (ADR 0008, 0015).

const enc = new TextEncoder();

function utf8(s) {
  return enc.encode(s);
}

// Decode UTF-8 strictly; null when the bytes are not UTF-8.
function fromUtf8(bytes) {
  try {
    return new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(bytes);
  } catch {
    return null;
  }
}

function concatBytes(chunks) {
  let n = 0;
  for (const c of chunks) n += c.length;
  const out = new Uint8Array(n);
  let o = 0;
  for (const c of chunks) {
    out.set(c, o);
    o += c.length;
  }
  return out;
}

// --- CRC-32 (zip) ----------------------------------------------------------------

let CRC_TABLE = null;

function crc32(bytes) {
  if (CRC_TABLE === null) {
    CRC_TABLE = new Uint32Array(256);
    for (let n = 0; n < 256; n++) {
      let c = n;
      for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
      CRC_TABLE[n] = c >>> 0;
    }
  }
  let c = 0xffffffff;
  for (let i = 0; i < bytes.length; i++) c = CRC_TABLE[(c ^ bytes[i]) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}

// --- SHA-256 ----------------------------------------------------------------------

const SHA_K = new Uint32Array([
  0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
  0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
  0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
  0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
  0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
  0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
  0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
  0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
]);

function sha256Hex(bytes) {
  const h = new Uint32Array([0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]);
  const len = bytes.length;
  const padded = new Uint8Array(((len + 9 + 63) >> 6) << 6);
  padded.set(bytes);
  padded[len] = 0x80;
  const bits = len * 8;
  const view = new DataView(padded.buffer);
  view.setUint32(padded.length - 8, Math.floor(bits / 0x100000000));
  view.setUint32(padded.length - 4, bits >>> 0);
  const wbuf = new Uint32Array(64);
  for (let off = 0; off < padded.length; off += 64) {
    for (let t = 0; t < 16; t++) wbuf[t] = view.getUint32(off + t * 4);
    for (let t = 16; t < 64; t++) {
      const a = wbuf[t - 15], b = wbuf[t - 2];
      const s0 = ((b >>> 17) | (b << 15)) ^ ((b >>> 19) | (b << 13)) ^ (b >>> 10);
      const s1 = ((a >>> 7) | (a << 25)) ^ ((a >>> 18) | (a << 14)) ^ (a >>> 3);
      wbuf[t] = (s0 + wbuf[t - 7] + s1 + wbuf[t - 16]) | 0;
    }
    let [a, b, c, d, e, f, g, hh] = h;
    for (let t = 0; t < 64; t++) {
      const t1 = (hh + (((e >>> 6) | (e << 26)) ^ ((e >>> 11) | (e << 21)) ^ ((e >>> 25) | (e << 7))) + ((e & f) ^ (~e & g)) + SHA_K[t] + wbuf[t]) | 0;
      const t2 = ((((a >>> 2) | (a << 30)) ^ ((a >>> 13) | (a << 19)) ^ ((a >>> 22) | (a << 10))) + ((a & b) ^ (a & c) ^ (b & c))) | 0;
      hh = g; g = f; f = e; e = (d + t1) | 0; d = c; c = b; b = a; a = (t1 + t2) | 0;
    }
    h[0] += a; h[1] += b; h[2] += c; h[3] += d; h[4] += e; h[5] += f; h[6] += g; h[7] += hh;
  }
  let out = "";
  for (let i = 0; i < 8; i++) out += (h[i] >>> 0).toString(16).padStart(8, "0");
  return out;
}

// --- Python's json.dumps(value, ensure_ascii=False) --------------------------------

// A number Python holds as a float: written with ".0" when it is whole.
class PyFloat {
  constructor(value) {
    this.value = value;
  }
}

function pyString(s) {
  let out = '"';
  for (const ch of s) {
    const cp = ch.codePointAt(0);
    if (ch === '"') out += '\\"';
    else if (ch === "\\") out += "\\\\";
    else if (ch === "\n") out += "\\n";
    else if (ch === "\r") out += "\\r";
    else if (ch === "\t") out += "\\t";
    else if (ch === "\b") out += "\\b";
    else if (ch === "\f") out += "\\f";
    else if (cp < 0x20) out += "\\u" + cp.toString(16).padStart(4, "0");
    else out += ch;
  }
  return out + '"';
}

function pyDumps(v) {
  if (v === null || v === undefined) return "null";
  if (v === true) return "true";
  if (v === false) return "false";
  if (v instanceof PyFloat) return Number.isInteger(v.value) ? v.value.toFixed(1) : String(v.value);
  if (typeof v === "number") return String(v);
  if (typeof v === "string") return pyString(v);
  if (Array.isArray(v)) return "[" + v.map(pyDumps).join(", ") + "]";
  return "{" + Object.keys(v).map((k) => pyString(k) + ": " + pyDumps(v[k])).join(", ") + "}";
}

// --- code points -------------------------------------------------------------------

// The full character at a UTF-16 index (a surrogate pair read whole).
function cpAt(s, i) {
  if (i < 0 || i >= s.length) return "";
  const c = s.charCodeAt(i);
  if (c >= 0xd800 && c <= 0xdbff && i + 1 < s.length) {
    const d = s.charCodeAt(i + 1);
    if (d >= 0xdc00 && d <= 0xdfff) return s.slice(i, i + 2);
  }
  return s[i];
}

// The full character that ends just before a UTF-16 index.
function cpBefore(s, i) {
  if (i <= 0) return "";
  const c = s.charCodeAt(i - 1);
  if (c >= 0xdc00 && c <= 0xdfff && i >= 2) {
    const d = s.charCodeAt(i - 2);
    if (d >= 0xd800 && d <= 0xdbff) return s.slice(i - 2, i);
  }
  return s[i - 1];
}

function codePointLength(s) {
  let n = 0;
  for (const _ of s) n++;
  return n;
}

function stripChars(s, chars) {
  let a = 0;
  let b = s.length;
  while (a < b && chars.indexOf(s[a]) !== -1) a++;
  while (b > a && chars.indexOf(s[b - 1]) !== -1) b--;
  return s.slice(a, b);
}

function rstripChars(s, chars) {
  let b = s.length;
  while (b > 0 && chars.indexOf(s[b - 1]) !== -1) b--;
  return s.slice(0, b);
}

// A regular expression matched exactly at `pos` (Python's pattern.match(s, pos)).
function matchAt(re, s, pos) {
  re.lastIndex = pos;
  const m = re.exec(s);
  return m;
}

// Regular expressions for matchAt must carry the sticky flag.
function sticky(source, flags) {
  return new RegExp(source, "y" + (flags || ""));
}

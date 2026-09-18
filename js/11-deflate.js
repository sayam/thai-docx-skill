// SPDX-FileCopyrightText: 2026 Sayam Sriphua
// SPDX-License-Identifier: MIT
// A deflate of this project's own — the port of thai_docx/deflate.py, byte for byte.
//
// `repair` rewrites parts of a package a user handed over, and ADR 0008 says the two
// implementations must write the same bytes. No two compression libraries promise that, so
// every choice a compressor is free to make is fixed in both: fixed-Huffman blocks, a chained
// hash of three bytes, a greedy match taken as soon as it is found, and an empty final block.
// The numbers below are the definition; changing one changes the output of both.

const DEFLATE_WINDOW = 32768;
const DEFLATE_MIN_MATCH = 3, DEFLATE_MAX_MATCH = 258;
const DEFLATE_HASH_BITS = 15;
const DEFLATE_MAX_CHAIN = 128;
const DEFLATE_BLOCK_BYTES = 1 << 16;

// RFC 1951 §3.2.5: the length and distance codes, and their extra bits.
const D_LEN_BASE = [3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 23, 27, 31, 35, 43, 51, 59,
  67, 83, 99, 115, 131, 163, 195, 227, 258];
const D_LEN_EXTRA = [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 0];
const D_DIST_BASE = [1, 2, 3, 4, 5, 7, 9, 13, 17, 25, 33, 49, 65, 97, 129, 193, 257, 385, 513, 769,
  1025, 1537, 2049, 3073, 4097, 6145, 8193, 12289, 16385, 24577];
const D_DIST_EXTRA = [0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13];

// Deflate's bit order: bits fill a byte from its least significant end, and a Huffman code is
// written from its most significant bit (RFC 1951 §3.1.1).
class DeflateBits {
  constructor() {
    this.out = [];
    this.bit = 0;
    this.acc = 0;
  }

  put(value, count) {
    this.acc |= (value & ((1 << count) - 1)) << this.bit;
    this.bit += count;
    while (this.bit >= 8) {
      this.out.push(this.acc & 0xff);
      this.acc >>>= 8;
      this.bit -= 8;
    }
  }

  putCode(code, count) {
    for (let i = count - 1; i >= 0; i--) this.put((code >>> i) & 1, 1);
  }

  finish() {
    if (this.bit) this.out.push(this.acc & 0xff);
    return new Uint8Array(this.out);
  }
}

// The fixed literal/length code of RFC 1951 §3.2.6.
function deflateLiteral(bits, value) {
  if (value < 144) bits.putCode(0b00110000 + value, 8);
  else if (value < 256) bits.putCode(0b110010000 + value - 144, 9);
  else if (value < 280) bits.putCode(value - 256, 7);
  else bits.putCode(0b11000000 + value - 280, 8);
}

function deflateLengthCode(length) {
  for (let i = D_LEN_BASE.length - 1; i >= 0; i--) if (length >= D_LEN_BASE[i]) return i;
  throw new ZipError("a match shorter than the shortest length code");
}

function deflateDistanceCode(distance) {
  for (let i = D_DIST_BASE.length - 1; i >= 0; i--) if (distance >= D_DIST_BASE[i]) return i;
  throw new ZipError("a match nearer than the nearest distance code");
}

// `data` as a raw deflate stream — what a zip entry of method 8 carries.
function deflate(data) {
  const bits = new DeflateBits();
  const size = data.length;
  const head = new Int32Array(1 << DEFLATE_HASH_BITS).fill(-1);
  const prev = new Int32Array(Math.max(size, 1)).fill(-1);
  let i = 0, blockStart = 0;
  // Every block of data carries BFINAL=0 and the stream is closed by an empty final block.
  // Ten bits, and the writer never has to know which block will turn out to be the last.
  if (size) {
    bits.put(0, 1);
    bits.put(1, 2);
  }
  while (i < size) {
    if (i - blockStart >= DEFLATE_BLOCK_BYTES) {
      deflateLiteral(bits, 256);
      bits.put(0, 1);
      bits.put(1, 2);
      blockStart = i;
    }
    let bestLen = 0, bestDist = 0;
    const longest = Math.min(DEFLATE_MAX_MATCH, size - i); // a match never runs past the end
    if (longest >= DEFLATE_MIN_MATCH) {
      const key = ((data[i] << 16) | (data[i + 1] << 8) | data[i + 2]) % (1 << DEFLATE_HASH_BITS);
      let at = head[key], steps = 0;
      const limit = i - DEFLATE_WINDOW; // -1 ends the chain, and a negative limit must not let it pass
      while (at >= 0 && at > limit && steps < DEFLATE_MAX_CHAIN) {
        steps += 1;
        // the byte past the best match so far: if it differs, this one cannot win
        if (data[at + bestLen] === data[i + bestLen]) {
          let length = 0;
          while (length < longest && data[at + length] === data[i + length]) length += 1;
          if (length > bestLen) {
            bestLen = length;
            bestDist = i - at;
            if (bestLen >= longest) break;
          }
        }
        at = prev[at];
      }
    }
    let taken;
    if (bestLen >= DEFLATE_MIN_MATCH) {
      const code = deflateLengthCode(bestLen);
      deflateLiteral(bits, 257 + code);
      bits.put(bestLen - D_LEN_BASE[code], D_LEN_EXTRA[code]);
      const dcode = deflateDistanceCode(bestDist);
      bits.putCode(dcode, 5);
      bits.put(bestDist - D_DIST_BASE[dcode], D_DIST_EXTRA[dcode]);
      taken = bestLen;
    } else {
      deflateLiteral(bits, data[i]);
      taken = 1;
    }
    for (let j = i; j < i + taken; j++) {
      if (j + DEFLATE_MIN_MATCH <= size) {
        const key = ((data[j] << 16) | (data[j + 1] << 8) | data[j + 2]) % (1 << DEFLATE_HASH_BITS);
        prev[j] = head[key];
        head[key] = j;
      }
    }
    i += taken;
  }
  if (size) deflateLiteral(bits, 256);
  bits.put(1, 1); // BFINAL
  bits.put(1, 2); // BTYPE: fixed Huffman
  deflateLiteral(bits, 256); // an empty block: nothing but its end
  return bits.finish();
}

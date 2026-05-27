#!/usr/bin/env python3
"""Pure-Python MPQ v1 writer for 3.3.5a (build 12340) client patches.

Implements just enough of Blizzard's MPQ ("Mo'PaQ") format to pack a
directory tree into a `patch-Z.MPQ`-style archive that WoW WotLK
loads:

* Single-unit files only (no sector array).
* zlib compression per file when it shrinks the data; raw otherwise.
* Encrypted hash + block tables (always required).
* No file-data encryption (we don't set MPQ_FILE_ENCRYPTED).
* Auto-generated (listfile) inside the archive.

Format reference: http://www.zezula.net/en/mpq/mpqformat.html
Cipher reference: http://www.zezula.net/en/mpq/stormstring.html

Why pure Python: the only PyPI MPQ writer (pympq) ships Windows wheels
only, and the C `libmpq` AzerothCore vendors is read-only. Writing the
Storm cipher + table builders from scratch is ~250 lines of code and
avoids vendoring StormLib + a C++ wrapper just to pack 6.5k files.
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path
from typing import Iterable


# --- Storm Buffer (1280-DWORD cipher table) ---------------------------------

_CRYPT_TABLE: list[int] | None = None


def _init_crypt_table() -> list[int]:
    global _CRYPT_TABLE
    if _CRYPT_TABLE is not None:
        return _CRYPT_TABLE
    table = [0] * 0x500
    seed = 0x00100001
    for index1 in range(0x100):
        index2 = index1
        for _ in range(5):
            seed = (seed * 125 + 3) % 0x2AAAAB
            temp1 = (seed & 0xFFFF) << 0x10
            seed = (seed * 125 + 3) % 0x2AAAAB
            temp2 = seed & 0xFFFF
            table[index2] = (temp1 | temp2) & 0xFFFFFFFF
            index2 += 0x100
    _CRYPT_TABLE = table
    return table


def _hash_string(name: str, hash_type: int) -> int:
    """Storm filename hash.

    hash_type:
      0 = table offset (lookup start slot in hash table)
      1 = nameA (stored in hash table entry)
      2 = nameB (stored in hash table entry)
      3 = file/table encryption key
    """
    table = _init_crypt_table()
    seed1 = 0x7FED7FED
    seed2 = 0xEEEEEEEE
    for ch in name:
        c = ord(ch)
        if c == ord('/'):
            c = ord('\\')
        if ord('a') <= c <= ord('z'):
            c = c - ord('a') + ord('A')
        seed1 = (table[(hash_type << 8) + c] ^ ((seed1 + seed2) & 0xFFFFFFFF)) & 0xFFFFFFFF
        seed2 = (c + seed1 + seed2 + (seed2 << 5) + 3) & 0xFFFFFFFF
    return seed1


def _encrypt_dwords(data: bytes, key: int) -> bytes:
    """Storm DWORD-stream cipher (encrypt). len(data) must be a multiple of 4."""
    table = _init_crypt_table()
    n = len(data) // 4
    out = bytearray(n * 4)
    key1 = key & 0xFFFFFFFF
    key2 = 0xEEEEEEEE
    for i in range(n):
        key2 = (key2 + table[0x400 + (key1 & 0xFF)]) & 0xFFFFFFFF
        plain = struct.unpack_from('<I', data, i * 4)[0]
        cipher = (plain ^ ((key1 + key2) & 0xFFFFFFFF)) & 0xFFFFFFFF
        struct.pack_into('<I', out, i * 4, cipher)
        # Storm key1 update: ((~key1 << 21) + 0x11111111) | (key1 >> 11).
        # Both references to key1 below resolve to the pre-update value
        # because Python evaluates the RHS fully before assigning.
        key1 = (
            (((((~key1) & 0xFFFFFFFF) << 0x15) & 0xFFFFFFFF) + 0x11111111)
            | (key1 >> 0x0B)
        ) & 0xFFFFFFFF
        key2 = (plain + key2 + (key2 << 5) + 3) & 0xFFFFFFFF
    return bytes(out)


def _decrypt_dwords(data: bytes, key: int) -> bytes:
    """Storm DWORD-stream cipher (decrypt). Symmetric except that key2's
    feedback is taken from the recovered plaintext, not the input."""
    table = _init_crypt_table()
    n = len(data) // 4
    out = bytearray(n * 4)
    key1 = key & 0xFFFFFFFF
    key2 = 0xEEEEEEEE
    for i in range(n):
        key2 = (key2 + table[0x400 + (key1 & 0xFF)]) & 0xFFFFFFFF
        cipher = struct.unpack_from('<I', data, i * 4)[0]
        plain = (cipher ^ ((key1 + key2) & 0xFFFFFFFF)) & 0xFFFFFFFF
        struct.pack_into('<I', out, i * 4, plain)
        key1 = (
            (((((~key1) & 0xFFFFFFFF) << 0x15) & 0xFFFFFFFF) + 0x11111111)
            | (key1 >> 0x0B)
        ) & 0xFFFFFFFF
        key2 = (plain + key2 + (key2 << 5) + 3) & 0xFFFFFFFF
    return bytes(out)


# --- Format constants -------------------------------------------------------

MPQ_FILE_EXISTS = 0x80000000
MPQ_FILE_SINGLE_UNIT = 0x01000000
MPQ_FILE_COMPRESS = 0x00000200
MPQ_FILE_ENCRYPTED = 0x00010000  # not used; reference only

# First-byte compression mask when MPQ_FILE_COMPRESS is set.
COMPRESS_ZLIB = 0x02
COMPRESS_BZIP2 = 0x10  # reference only

HASH_EMPTY = 0xFFFFFFFF
HASH_DELETED = 0xFFFFFFFE


def _next_pow2(n: int) -> int:
    p = 1
    while p < n:
        p <<= 1
    return p


# --- Writer -----------------------------------------------------------------

class MpqWriter:
    """Build an MPQ v1 archive from a set of source files / in-memory blobs.

    Usage:
        w = MpqWriter("output/patch-Z.MPQ")
        w.add_directory("staging/")                # walk + add everything
        w.add_data("(custom)\\stamp.txt", b"hi")   # in-memory blob
        files, size = w.write()
    """

    def __init__(self, output_path: str | Path, sector_size_shift: int = 3) -> None:
        # sector_size_shift=3 means 512 << 3 = 4096-byte sectors. We use
        # SINGLE_UNIT files exclusively, so this only affects how a reader
        # might interpret non-SINGLE_UNIT files (none of ours).
        self.output_path = Path(output_path)
        self.sector_size_shift = sector_size_shift
        self._entries: list[tuple[str, Path | bytes]] = []

    def add_file(self, src_path: str | Path, in_mpq_path: str) -> None:
        self._entries.append((in_mpq_path, Path(src_path)))

    def add_data(self, in_mpq_path: str, data: bytes) -> None:
        self._entries.append((in_mpq_path, bytes(data)))

    def add_directory(self, src_dir: str | Path, in_mpq_prefix: str = "") -> int:
        """Recursively add every file under src_dir, preserving relative paths.
        Returns the number of files added."""
        src_root = Path(src_dir)
        count = 0
        for p in sorted(src_root.rglob("*")):
            if not p.is_file():
                continue
            rel = p.relative_to(src_root).as_posix().replace('/', '\\')
            if in_mpq_prefix:
                rel = in_mpq_prefix.rstrip('\\') + '\\' + rel
            self.add_file(p, rel)
            count += 1
        return count

    def write(self) -> tuple[int, int]:
        """Write the archive. Returns (num_files_including_listfile, archive_size)."""
        # Normalize all in-MPQ paths to backslashes (the convention WoW uses
        # internally; the Storm hash function uppercases & normalizes anyway,
        # but the (listfile) text needs to be in canonical form).
        entries: list[tuple[str, Path | bytes]] = [
            (p.replace('/', '\\'), src) for p, src in self._entries
        ]

        # Auto-generate (listfile). CRLF-separated, trailing CRLF, matches
        # what Ladik's MPQ Editor emits.
        listfile_text = '\r\n'.join(p for p, _ in entries) + '\r\n'
        entries.append(('(listfile)', listfile_text.encode('utf-8')))

        num_files = len(entries)
        # Power-of-two hash table, sized for low collision risk (~50% load
        # factor max). Minimum 16 entries.
        hash_table_size = max(16, _next_pow2(num_files * 2))

        block_entries: list[tuple[int, int, int, int]] = []

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.output_path.with_suffix(self.output_path.suffix + '.tmp')

        try:
            with open(tmp_path, 'wb') as f:
                # Reserve the 44-byte v2 header; we patch it after we know
                # the final hash/block table offsets.
                f.write(b'\x00' * 44)

                for _in_mpq_path, src in entries:
                    raw = src if isinstance(src, bytes) else src.read_bytes()
                    unpacked_size = len(raw)
                    file_pos = f.tell()
                    if unpacked_size == 0:
                        # Empty file: EXISTS + SINGLE_UNIT, no body. WoW
                        # tolerates these; (attributes) etc. are sometimes
                        # zero-length.
                        packed_size = 0
                        flags = MPQ_FILE_EXISTS | MPQ_FILE_SINGLE_UNIT
                    else:
                        compressed = zlib.compress(raw, 6)
                        # Compression only wins if the 1-byte mask plus zlib
                        # payload is smaller than the raw bytes. BLPs, M2s,
                        # OGGs are already entropy-dense and usually fail
                        # this test; small text files always win.
                        if 1 + len(compressed) < unpacked_size:
                            f.write(bytes([COMPRESS_ZLIB]))
                            f.write(compressed)
                            packed_size = 1 + len(compressed)
                            flags = (
                                MPQ_FILE_EXISTS
                                | MPQ_FILE_SINGLE_UNIT
                                | MPQ_FILE_COMPRESS
                            )
                        else:
                            f.write(raw)
                            packed_size = unpacked_size
                            flags = MPQ_FILE_EXISTS | MPQ_FILE_SINGLE_UNIT
                    block_entries.append((file_pos, packed_size, unpacked_size, flags))

                # Build hash table with linear-probe insertion.
                hash_table: list[list[int]] = [
                    [HASH_EMPTY, HASH_EMPTY, 0, 0, HASH_EMPTY]
                    for _ in range(hash_table_size)
                ]
                for block_index, (in_mpq_path, _) in enumerate(entries):
                    start = _hash_string(in_mpq_path, 0) & (hash_table_size - 1)
                    name_a = _hash_string(in_mpq_path, 1)
                    name_b = _hash_string(in_mpq_path, 2)
                    slot = start
                    probes = 0
                    while hash_table[slot][4] != HASH_EMPTY:
                        slot = (slot + 1) & (hash_table_size - 1)
                        probes += 1
                        if probes >= hash_table_size:
                            raise RuntimeError(
                                "Hash table full - sizing bug "
                                f"(size={hash_table_size}, files={num_files})"
                            )
                    hash_table[slot] = [name_a, name_b, 0, 0, block_index]

                # Serialize + encrypt hash table.
                hash_buf = bytearray()
                for entry in hash_table:
                    hash_buf.extend(
                        struct.pack(
                            '<IIHHI',
                            entry[0], entry[1], entry[2], entry[3], entry[4],
                        )
                    )
                hash_key = _hash_string("(hash table)", 3)
                hash_enc = _encrypt_dwords(bytes(hash_buf), hash_key)

                # Serialize + encrypt block table.
                block_buf = bytearray()
                for entry in block_entries:
                    block_buf.extend(struct.pack('<IIII', *entry))
                block_key = _hash_string("(block table)", 3)
                block_enc = _encrypt_dwords(bytes(block_buf), block_key)

                # Write tables (hash first, then block; matches StormLib's
                # default layout for new archives).
                hash_table_pos = f.tell()
                f.write(hash_enc)
                block_table_pos = f.tell()
                f.write(block_enc)
                archive_size = f.tell()

                # Patch the header.
                # WoW 3.3.5a's loader silently rejects format v1 (v0 in the
                # version field, header_size=32). Blizzard's locale patches
                # are all format v2 (v1 in the version field, header_size=44)
                # which adds 8 bytes of 64-bit archive size + 4 bytes of
                # high-word hash/block table positions. For archives < 4GB
                # the new fields are all zero, but the size and version
                # fields must match v2 or the archive is ignored.
                f.seek(0)
                f.write(struct.pack(
                    '<4sIIHHIIII',
                    b'MPQ\x1a',
                    44,                         # header size (v2)
                    archive_size,               # archive size (low 32 bits)
                    1,                          # format version (1 = v2)
                    self.sector_size_shift,
                    hash_table_pos,
                    block_table_pos,
                    hash_table_size,
                    num_files,                  # block table size
                ))
                # v2 extension: 64-bit archive size + 16-bit high positions.
                f.write(struct.pack(
                    '<QHH',
                    archive_size,               # archive_size_64
                    0,                          # hash_table_pos_hi
                    0,                          # block_table_pos_hi
                ))

            # Atomic rename so partial archives never replace a prior good one.
            tmp_path.replace(self.output_path)
        except Exception:
            if tmp_path.exists():
                tmp_path.unlink()
            raise

        return num_files, archive_size


# --- Reader (used for post-pack self-verification) --------------------------

class MpqReader:
    """Minimal MPQ v1 reader. Only handles the subset we write: SINGLE_UNIT
    files, optional zlib compression, no file-data encryption. Used by
    build_patch.py to round-trip-verify a freshly packed archive."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._f = open(self.path, 'rb')
        magic = self._f.read(4)
        if magic != b'MPQ\x1a':
            raise ValueError(f"Not an MPQ archive (magic={magic!r})")
        rest = self._f.read(28)
        (
            self.header_size,
            self.archive_size,
            self.format_version,
            self.sector_shift,
            hash_pos,
            block_pos,
            self.hash_table_size,
            self.block_table_size,
        ) = struct.unpack('<IIHHIIII', rest)
        if self.format_version not in (0, 1):
            raise ValueError(
                f"Only v1/v2 archives supported (got v{self.format_version + 1})"
            )
        # For v2 we ignore the extended fields (we only handle <4GB archives).
        if self.format_version == 1 and self.header_size >= 44:
            self._f.read(12)

        self._f.seek(hash_pos)
        hash_enc = self._f.read(self.hash_table_size * 16)
        hash_dec = _decrypt_dwords(hash_enc, _hash_string("(hash table)", 3))
        self.hash_table: list[tuple[int, int, int, int, int]] = []
        for i in range(self.hash_table_size):
            self.hash_table.append(
                struct.unpack_from('<IIHHI', hash_dec, i * 16)
            )

        self._f.seek(block_pos)
        block_enc = self._f.read(self.block_table_size * 16)
        block_dec = _decrypt_dwords(block_enc, _hash_string("(block table)", 3))
        self.block_table: list[tuple[int, int, int, int]] = []
        for i in range(self.block_table_size):
            self.block_table.append(
                struct.unpack_from('<IIII', block_dec, i * 16)
            )

    def find(self, name: str) -> int | None:
        start = _hash_string(name, 0) & (self.hash_table_size - 1)
        name_a = _hash_string(name, 1)
        name_b = _hash_string(name, 2)
        slot = start
        for _ in range(self.hash_table_size):
            ha, hb, _loc, _plat, bi = self.hash_table[slot]
            if bi == HASH_EMPTY:
                return None
            if ha == name_a and hb == name_b and bi != HASH_DELETED:
                return bi
            slot = (slot + 1) & (self.hash_table_size - 1)
        return None

    def read(self, name: str) -> bytes:
        block_index = self.find(name)
        if block_index is None:
            raise KeyError(name)
        fp, ps, us, fl = self.block_table[block_index]
        if not (fl & MPQ_FILE_EXISTS):
            raise KeyError(f"{name} marked non-existent in block table")
        if not (fl & MPQ_FILE_SINGLE_UNIT):
            raise NotImplementedError(
                f"Sector-based files not supported by this reader ({name})"
            )
        if us == 0:
            return b''
        self._f.seek(fp)
        if fl & MPQ_FILE_COMPRESS:
            mask_byte = self._f.read(1)
            if not mask_byte:
                raise ValueError(f"Truncated compressed file: {name}")
            mask = mask_byte[0]
            blob = self._f.read(ps - 1)
            if mask & COMPRESS_ZLIB:
                return zlib.decompress(blob)
            raise NotImplementedError(
                f"Unsupported compression mask 0x{mask:02x} on {name}"
            )
        return self._f.read(ps)

    def listfile(self) -> list[str]:
        """Returns the parsed (listfile), or [] if not present."""
        try:
            text = self.read('(listfile)').decode('utf-8', errors='replace')
        except KeyError:
            return []
        return [line for line in text.split('\r\n') if line]

    def close(self) -> None:
        self._f.close()

    def __enter__(self) -> 'MpqReader':
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

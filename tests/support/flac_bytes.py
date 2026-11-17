# SPDX-License-Identifier: MPL-2.0

"""Synthetic FLAC byte construction shared by tests."""

from collections.abc import Sequence
from pathlib import Path


def streaminfo_payload() -> bytes:
    payload = bytearray()
    # state min/max block sizes of 4096
    payload += (4096).to_bytes(2, "big") * 2
    # state min/max frame sizes of 0 (unknown value)
    payload += (0).to_bytes(3, "big") * 2

    # begin construction of audio properties payload
    sample_rate = 44_100
    channels = 2
    bits_per_sample = 16
    total_samples = 44_100

    # sample rate (20), channels - 1 (3), bit depth - 1 (5), samples (36)
    sample_rate_bits = sample_rate << (64 - 20)
    channel_bits = (channels - 1) << (64 - 20 - 3)
    bit_depth_bits = (bits_per_sample - 1) << 36
    total_samples_bits = total_samples

    packed = sample_rate_bits | channel_bits | bit_depth_bits | total_samples_bits
    payload += packed.to_bytes(8, "big")

    # 16 empty bytes for PCM MD5 signature (unset)
    payload += b"\x00" * 16

    assert len(payload) == 34  # bytes
    return bytes(payload)


def vorbis_payload(
    raw_entries: Sequence[bytes],
    vendor: bytes = b"test",
    declared_count: int | None = None,
) -> bytes:
    # vorbis comments use 32-bit little-endian lengths and counts
    uint32_bytes = 4

    if declared_count is None:
        declared_count = len(raw_entries)

    payload = bytearray()

    # vendor string: length + raw bytes
    vendor_length = len(vendor).to_bytes(uint32_bytes, "little")
    payload += vendor_length
    payload += vendor

    # number of comment entries
    entry_count = declared_count.to_bytes(uint32_bytes, "little")
    payload += entry_count

    # each comment: length + raw bytes
    for entry in raw_entries:
        entry_length = len(entry).to_bytes(uint32_bytes, "little")
        payload += entry_length
        payload += entry

    return bytes(payload)


def flac_bytes(comment_payloads: Sequence[bytes]) -> bytes:
    # FLAC metadata block types
    streaminfo_type = 0
    vorbis_comment_type = 4

    # metadata block header:
    # 1 bit: last-block flag
    # 7 bits: block type
    # 24 bits: payload length

    last_block_flag = 1 << 7
    block_length_bytes = 3

    blocks = [(streaminfo_type, streaminfo_payload())]
    blocks.extend((vorbis_comment_type, payload) for payload in comment_payloads)

    # native flac file signature
    data = bytearray(b"fLaC")

    for index, (block_type, payload) in enumerate(blocks):
        is_last_block = index == len(blocks) - 1

        header_type = block_type | (last_block_flag if is_last_block else 0)
        block_length = len(payload).to_bytes(block_length_bytes, "big")

        data.append(header_type)
        data += block_length
        data += payload

    return bytes(data)


def write_flac(path: Path, *comment_payloads: bytes) -> Path:
    path.write_bytes(flac_bytes(comment_payloads))
    return path

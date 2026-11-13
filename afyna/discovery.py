"""Find file paths without reading file contents or changing source files."""

import errno
import os
import stat
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DiscoveryError:
    path: Path
    error: OSError


@dataclass
class FileDiscoveryInventory:
    files: list[Path] = field(default_factory=list)
    errors: list[DiscoveryError] = field(default_factory=list)


@dataclass(frozen=True)
class DirectoryIdentity:
    filesystem_device_id: int
    inode_number: int


@dataclass(frozen=True)
class TraversalCandidate:
    path: Path
    ancestor_directory_identities: frozenset[DirectoryIdentity]


def get_source_directory() -> Path:
    """Obtain the source directory for afyna's operations."""
    return Path.cwd()


def discover_files(source_directory: Path) -> FileDiscoveryInventory:
    """Find regular files recursively, following file and directory symlinks.

    Returns sorted absolute paths and filesystem errors. Keeps symlink names
    and ``..`` in paths instead of resolving them.
    """
    if not source_directory.is_absolute():
        raise ValueError("source_directory must be an absolute path")

    inventory = FileDiscoveryInventory()
    traversal_candidates: list[TraversalCandidate] = [
        TraversalCandidate(
            path=source_directory,
            ancestor_directory_identities=frozenset(),
        )
    ]

    while traversal_candidates:
        candidate = traversal_candidates.pop()
        path = candidate.path
        ancestor_identities: frozenset[DirectoryIdentity] = (
            candidate.ancestor_directory_identities
        )

        try:
            observed_stat = os.stat(path)
        except OSError as error:
            inventory.errors.append(DiscoveryError(path, error))
            continue

        if not stat.S_ISDIR(observed_stat.st_mode):
            if path == source_directory:
                error = NotADirectoryError(
                    errno.ENOTDIR, "source is not a directory", str(path)
                )
                inventory.errors.append(DiscoveryError(path, error))
            elif stat.S_ISREG(observed_stat.st_mode):
                inventory.files.append(path)
            continue

        filesystem_device_id = observed_stat.st_dev
        inode_number = observed_stat.st_ino
        if filesystem_device_id is None or inode_number in (None, 0):
            error = OSError(errno.EIO, "directory identity unavailable", str(path))
            inventory.errors.append(DiscoveryError(path, error))
            continue

        directory_identity = DirectoryIdentity(
            filesystem_device_id=filesystem_device_id,
            inode_number=inode_number,
        )

        # avoid loops back to ancestor directories, but allow other aliases
        # prevent infinite stack growth until OOM
        if directory_identity in ancestor_identities:
            continue

        child_ancestors = ancestor_identities | {directory_identity}

        try:
            with os.scandir(path) as entries:
                for entry in entries:
                    # keep entries already found if enumeration later fails
                    traversal_candidates.append(
                        TraversalCandidate(
                            path=path / entry.name,
                            ancestor_directory_identities=child_ancestors,
                        )
                    )
        except OSError as error:
            inventory.errors.append(DiscoveryError(path, error))

    inventory.files.sort(key=str)
    return inventory

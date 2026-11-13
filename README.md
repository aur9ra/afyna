<div align="center">
  <img src=".github/assets/afyna.png" alt="Pixel art containing a harp and 'afyna' in stylized lettering">
</div>

afyna is an interactive music library organizer for importing music from messy downloads
into a coherent library.

afyna is designed for deliberate imports. **You choose what to organize, and you see
a preview of what will happen before any files are moved, copied, or changed.**

## 🪉 why? 🪉

Downloaded music often does not arrive in consistent layouts, nor in a file structure
ready to merge into your library.

afyna uses metadata to suggest album groupings and let you decide how downloaded music
is imported to your library.

## 🪉 albums 🪉

afyna treats an album as a group inferred from file metadata, rather than exclusively from
directories on disk.

afyna allows you to select the albums you'd like to import. afyna does not aim to edit tags,
transcode audio, fetch release data, or automatically organize download trees.

## 🪉 imports 🪉

Before an import is executed, afyna will show the proposed destinations for audio and selected
image files, alongside any proposed removal of original files. Execution requires your approval.

When missing information, conflicting evidence, or file collisions prevent safe operation, afyna
asks you to resolve the issue or refuses to proceed, rather than perform a potentially unsafe action
on its own.

Imports preserve file contents byte-for-byte.

## 🪉 status 🪉

afyna is in early development, and is currently not in a usable state. The behavior described above
is afyna's intended direction.

## 🪉 licensing 🪉

afyna's source code is licensed under [MPL-2.0](LICENSE).

The original logo at [`.github/assets/afyna.png`](.github/assets/afyna.png) is dedicated under [CC0-1.0](https://creativecommons.org/publicdomain/zero/1.0/legalcode).
Test media is separately licensed and attributed in [tests/fixtures/SOURCES.md](tests/fixtures/SOURCES.md),
and is not covered by the source-code license declaration.

Mutagen 1.48.1 is independently licensed under GPL-2.0-or-later. Distributing a combined
application must comply with applicable GPL terms, including relevant license/notice and
source-availability requirements. afyna's MPL-2.0 source license and package metadata do not
by themselves satisfy those obligations. Not every distribution arrangement has been legally assessed.

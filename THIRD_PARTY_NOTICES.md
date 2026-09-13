# Third-party notices for the Path 1 Windows EXE

The repository's own source remains under the MIT license in [`LICENSE`](LICENSE). A locally built
`video-autopilot-path1.exe` also contains independent third-party components under their own
licenses. The MIT license does not replace those terms.

## FFmpeg and ffprobe

`build_exe.py` embeds the `ffmpeg` and `ffprobe` executables resolved from the builder's `PATH`.
The build fails when either executable is missing, when the binary distribution does not include
its `LICENSE` and `README.txt`, or when FFmpeg reports `--enable-nonfree`.

The verified Windows build used for v0.13.0 is Gyan's static FFmpeg 9.0 full build. Its configuration
contains `--enable-gpl --enable-version3`, so those two binaries are GPL-3.0-or-later components.
The app invokes them as separate programs; it does not relink or relicense them. Build output places
their original license and build README beside the EXE as `FFmpeg-GPLv3.txt` and
`FFmpeg-BUILD-README.txt` and records hashes in `path1-build-info.json`.

- FFmpeg legal and license guidance: <https://ffmpeg.org/legal.html>
- Gyan Windows builds and matching source links: <https://www.gyan.dev/ffmpeg/builds/>
- FFmpeg source mirror and license texts: <https://github.com/FFmpeg/FFmpeg>

Anyone redistributing the EXE package is responsible for preserving these files and satisfying the
applicable FFmpeg/GPL source-availability requirements. This notice is operational guidance, not
legal advice.

## Python, PyInstaller, NumPy, and Pillow

- Python retains the Python Software Foundation License.
- PyInstaller is GPL-licensed with its documented exception for distributing generated bundles.
- NumPy retains its BSD-3-Clause license.
- Pillow retains its MIT-CMU license.

PyInstaller's collected package metadata and license files remain in the generated application
where provided by the installed wheels. Release packaging must keep this notice with the EXE.

# arco
Yet another Unit Generator library, with control via O2.

Try this:

`cd ugg`
`python3 ugtest.py`

Use CMake in `ugg/src/framework` to generate a project file.

Be sure to set `PORTAUDIO_LIB` and `PORTAUDIO_INCLUDE` variables in CMake.

Compile the project (`uggtest`)

Subdirectories:

- `arco` has code to test O2 intra-process/inter-thread communication

- `ugg` UGG-related stuff

    - `code` auto-generated by ugg

    - `ugg` Python unit generator generator + unit generator
                descriptions

    - `framework` One audio framework for running UGG code


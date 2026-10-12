# The PolyKybd render toolchain: KiCad 9 (exports the boards for the scene), Blender 4.1
# (with its bundled Python for the compositor), ffmpeg, the fonts the keycap screens
# use, and a Python for the PolyKybdHost preview tools. The repos and the scene are MOUNTED, not copied: see
# README.md. Build: docker build -t polykybd-render render/docker
FROM ubuntu:24.04

ARG BLENDER_VERSION=4.1.1
ENV DEBIAN_FRONTEND=noninteractive

# Blender's runtime libraries (it is a GUI build run headless), ffmpeg, and the fonts:
# FreeSansBold for the status panels, DejaVu for the storyboard captions, IPA Gothic
# for a CJK name spelled on the keys
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl xz-utils ffmpeg python3 python3-venv \
        libgl1 libegl1 libxi6 libxxf86vm1 libxfixes3 libxrender1 libxkbcommon0 libsm6 libice6 libx11-6 \
        fonts-freefont-ttf fonts-dejavu-core fonts-ipafont-gothic \
    && rm -rf /var/lib/apt/lists/*

# KiCad 9 from its release PPA, with the stock 3D models (~3 GB) the boards' parts use;
# render/export_boards.sh runs kicad-cli under xvfb-run
ARG KICAD_SERIES=9.0
RUN apt-get update && apt-get install -y --no-install-recommends gnupg xvfb xauth \
    && curl -sSL "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x245D5502FAD7A805" \
        | gpg --dearmor -o /usr/share/keyrings/kicad.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/kicad.gpg] https://ppa.launchpadcontent.net/kicad/kicad-${KICAD_SERIES}-releases/ubuntu noble main" \
        > /etc/apt/sources.list.d/kicad.list \
    && apt-get update && apt-get install -y --no-install-recommends kicad kicad-packages3d \
    && rm -rf /var/lib/apt/lists/*

# the official Linux build, the same one the renders were made with
RUN curl -sSL "https://download.blender.org/release/Blender${BLENDER_VERSION%.*}/blender-${BLENDER_VERSION}-linux-x64.tar.xz" \
        | tar -xJ -C /opt \
    && ln -s "/opt/blender-${BLENDER_VERSION}-linux-x64/blender" /usr/local/bin/blender
# the compositor (tutorial_video.py) runs on Blender's bundled Python, for its OpenImageIO
# and OpenColorIO; Pillow is the one module it needs that Blender does not ship
RUN /opt/blender-${BLENDER_VERSION}-linux-x64/${BLENDER_VERSION%.*}/python/bin/python3.11 -m ensurepip \
    && /opt/blender-${BLENDER_VERSION}-linux-x64/${BLENDER_VERSION%.*}/python/bin/python3.11 -m pip install \
        --no-cache-dir pillow==12.3.0

# tutorial_story.py imports PolyKybdHost's preview tools (tools/oled_preview.py and friends)
RUN python3 -m venv /opt/hostpy \
    && /opt/hostpy/bin/pip install --no-cache-dir numpy==2.4.6 pillow==12.3.0 openpyxl==3.1.5 fonttools==4.66.1

ENV BLENDER=blender HOSTPY=/opt/hostpy/bin/python
# /work holds PolyKybd, PolyKybdHost and qmk_firmware side by side
WORKDIR /work/PolyKybd
# "scene" builds render/out/hero.blend; anything else goes to render/tutorial_build.sh
ENTRYPOINT ["render/docker/entry.sh"]

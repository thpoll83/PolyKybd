# Rendering the tutorial video in a container

The first-run tutorial video takes hours on a CPU. This image holds everything the
render needs, KiCad and Blender included, so the machine needs Docker and nothing else.
It runs on the machine's GPU if it has one.

## What you need on the machine

- Docker.
- Three checkouts side by side in one folder: `PolyKybd` on `video/eden-tutorial`,
  `PolyKybdHost` on `fix/lang-layer-demo-column-glyphs` (its `main` draws the Lang menu's
  flags wrongly; the story stops with a message if the branch is wrong) and `qmk_firmware`
  on `PolyKybd` (only `keyboards/polykybd/` is read; no submodules needed).
- The scene `PolyKybd/render/out/hero.blend` (367 MB, not in git). The image builds it
  (below), or copy an existing one there.

## Build and run

```bash
cd <folder with the three checkouts>
docker build -t polykybd-render PolyKybd/render/docker

# once: export both boards with KiCad and build render/out/hero.blend (~30 min on 4 cores)
docker run --rm -v "$PWD":/work polykybd-render scene

# CPU only
docker run --rm -v "$PWD":/work polykybd-render 1024

# NVIDIA GPU (needs the NVIDIA Container Toolkit on the host)
docker run --rm --gpus all -e PK_GPU=OPTIX -v "$PWD":/work polykybd-render 2048

# AMD GPU (a ROCm-supported card)
docker run --rm --device /dev/kfd --device /dev/dri -e PK_GPU=HIP -v "$PWD":/work polykybd-render 2048
```

The arguments are `width samples outdir` (defaults `1024 32 render/out/tutorial_<width>`).
The video lands in `PolyKybd/render/out/tutorial_<width>/tutorial_<width>.mp4`, owned by
root; `--user "$(id -u):$(id -g)"` on `docker run` avoids that.

- It resumes: every render layer is a file, and one already on disk is skipped. Stop it
  any time and run the same command again. Delete the out folder to start over (for
  example after the shot list changes).
- `PK_GPU` falls back to the CPU with a note in the logs if no such device is found,
  so a wrong guess costs only speed. `OPTIX` is for RTX cards, `CUDA` for older NVIDIA.
- Which card you have: `lspci | grep -iE 'vga|3d|display'`; `nvidia-smi` works only
  with the NVIDIA driver installed.
- Progress is in `build.log` in the out folder; each Blender run logs beside it.

The image is about 5 GB, most of it KiCad's stock 3D models, which the board export
needs. At 2048 px the CPU run takes about 7.5 hours on 4 cores; a recent GPU should bring it
under an hour. The encode at the end runs on the CPU either way. It splits the frames over
one process per core (at most 16; `-e PK_JOBS=N` sets the number), each needing a few GB
of RAM at 2048 px, and joins the pieces without re-encoding.

## The assembly video

The left half built part by part on a white desk, then both halves and the USB cables
(47 s, `render/assembly_video.py`). It needs `PolyKybd` on `video/assembly` and the same
`render/out/hero.blend`; PolyKybdHost and qmk_firmware are not read.

```bash
docker build -t polykybd-render PolyKybd/render/docker        # again: the image gained Blender 5.1 and pcb2blender
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/work polykybd-render assembly 1920 32
```

The arguments are `width samples outdir` (defaults `1920 32 render/out/assembly_<width>`).
The first run builds three scenes in `render/out/` and keeps them: `assembly.blend` (the
left half as one object per part, ~15 min), `pcb_left.blend` (pcb2blender's board, ~5 min)
and `assembly_pcb.blend` (both put together). Then it renders 1176 frames into
`<outdir>/frames/`, `PK_JOBS` Blender processes side by side (default one per 8 cores, each
holding about 4 GB), and encodes `<outdir>/assembly_<width>.mp4` once all are there.

- It resumes: a frame on disk is skipped, so stop it and run the same command again.
- `-e PK_FRAMES="1 300"` renders only those frames, for a first look.
- `-e PK_GPU=OPTIX` (with `--gpus all`) renders on the GPU, one job by default.
- After a board change, delete `render/out/assembly*.blend`, `render/out/left.pcb3d`
  and `render/out/pcb_left.blend`; they are rebuilt on the next run.

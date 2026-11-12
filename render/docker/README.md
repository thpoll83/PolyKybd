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

## The MIDI video (Für Elise on the MIDI layer)

The same image renders the MIDI layer video (`render/midi_build.sh`). It needs the same
three checkouts, with `PolyKybd` on `render/workspaces` and `PolyKybdHost` on `main`, and
the scene `render/out/hero.blend` (build it with `scene` as above).

```bash
cd <folder with the three checkouts>
docker build -t polykybd-render PolyKybd/render/docker

# a quick look at the camera path: 480 px, 8 samples, every 2nd frame (about 1 h on 4 cores)
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/work polykybd-render midi-anim 480 8 25 2

# the moving-camera video: width samples fps step (defaults 1280 64 25 1)
docker run --rm --user "$(id -u):$(id -g)" --gpus all -e PK_GPU=OPTIX -v "$PWD":/work polykybd-render midi-anim 1920 64

# the fixed-camera video and its GIF: width samples (defaults 2560 256)
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/work polykybd-render midi-fixed
```

- `midi-anim` renders every frame in Cycles (1,150 at 25 fps), so it is the slow one:
  about 7 s a frame at 360 px and 6 samples on 4 CPU cores, and it grows with pixels times
  samples. Use a GPU (`PK_GPU`, as above) for anything past a preview. Frames land in
  `PolyKybd/render/out/midi_anim_<width>/`, the video beside them as
  `midi_anim_<width>.mp4`.
- `midi-fixed` renders 14 layers once and composes the frames in 2D: about 3 h at 2560 px
  and 256 samples on 4 CPU cores, then a few minutes for the frames. Output:
  `render/out/midi_fixed_<width>.mp4` and `.gif`.
- Both resume. Delete the frame or layer folder to start over, for example after the
  camera path (`SHOTS` in `render/midi_anim.py`) or the shot list changes.
- ⚠️ Give the container at least 8 GB of RAM: one Blender holds about 6 GB with the scene.
- The soundtrack plays the Salamander Grand Piano (CC BY 3.0). Credit it where the video
  is published: "Piano: Salamander Grand Piano by Alexander Holm, CC BY 3.0".

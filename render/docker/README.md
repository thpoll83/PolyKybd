# Rendering the tutorial video in a container

The first-run tutorial video takes hours on a CPU. This image holds everything the
render needs, so it can run on any Linux machine, and on its GPU if it has one.

## What you need on the machine

- Docker.
- Three checkouts side by side in one folder, on the branch with the video scripts:
  `PolyKybd`, `PolyKybdHost` and `qmk_firmware` (only `keyboards/polykybd/` is read;
  no submodules needed).
- The scene `PolyKybd/render/out/hero.blend` (367 MB, not in git). Rebuilding it is
  `render/README.md`, section 2, and needs KiCad; copying an existing one is easier.

## Build and run

```bash
cd <folder with the three checkouts>
docker build -t polykybd-render PolyKybd/render/docker

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

At 2048 px the CPU run takes about 7.5 hours on 4 cores; a recent GPU should bring it
under an hour. The encode at the end runs on the CPU either way (about an hour at 2048).

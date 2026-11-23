# mini_pupper_4_rl

A library of reinforcement-learning policies for the Mini Pupper v4. Each policy has one folder with everything about it:
its page, its training code, the recipes that trained it, the exported policies and checkpoints for each robot, and its
evaluation. The code the policies share (the policy interface, export, PPO, the simulation environment, the robot side)
lives in one common package.

## Policies

| | Policy | What it does | Robots |
|---|---|---|---|
| <img src="mp4_rl/skills/walker/media/sku2_walk.gif" width="200" alt="The walker"> | [Walker](mp4_rl/skills/walker/) | Walks in every direction, turns in place and rides out shoves; climbs the printed stairs and walks on rough ground in simulation | SKU2, SKU1 |
| <img src="mp4_rl/skills/getup/media/sku2_getup.gif" width="200" alt="The get-up"> | [Get-up](mp4_rl/skills/getup/) | Gets the robot back on its feet from any fall pose, with or without the lidar, and hands back to the walker | SKU2, SKU1 |

Each policy's page gives what it is, how it was trained, its results on the robots, how to evaluate it and how to run it
on the robot. Adding a policy: [docs/ADDING_A_POLICY.md](docs/ADDING_A_POLICY.md).

## Robots and the simulation

- **SKU2:** the long body with a Raspberry Pi 5 and the 3S LiPo inside.
- **SKU1:** the short body on the same legs, servos and ESP32 board, without a Raspberry Pi.

The robot models, their measured data (calibration, joint limits, masses), the servo models and the simulation scenes
come from [mini_pupper_4_sim](https://github.com/mangdangroboticsclub/mini_pupper_4_sim) (package `mp4_sim`), pinned
at release v0.2.0. Every trainer, evaluator and the exporter take `--robot sku2|sku1` (default `sku2`; an evaluator
defaults to the policy's own robot).

## Install

```bash
git clone https://github.com/mangdangroboticsclub/mini_pupper_4_rl.git && cd mini_pupper_4_rl
bash scripts/install/install.sh        # installs mp4-sim v0.2.0 too; see docs/INSTALL.md
CUDA_VISIBLE_DEVICES="" .venv/bin/python -m pytest tests/cpu         # no GPU needed
```

Training and evaluation need an NVIDIA GPU; without one the installer picks CPU mode (policy checks, export, the runner
on a simulated board, the CPU tests). The installer is for Linux and macOS. `MP4_SIM_SOURCE` installs `mp4-sim` from
elsewhere (a `mini_pupper_4_sim` checkout, or a pip URL such as `git+file:///path/to/mini_pupper_4_sim@v0.2.0`). Run
the commands in this repository from its root, without an inherited `PYTHONPATH` (`env -u PYTHONPATH` in front if your
shell sets one).

## Deployment

- **SKU2:** one runner on the Raspberry Pi, `python3 -m mp4_rl.deploy.runner`, runs the walker and switches to the
  get-up on a detected fall; it sends servo targets over UART to the ESP32 board running the
  [Mini Pupper v4 firmware](https://github.com/mangdangroboticsclub/minipupper_4_mcu). `tools/deploy.sh` copies the
  runner and the policy folders to the Pi, which needs only numpy and pyserial:
  [the SKU2 robot guide](mp4_rl/skills/getup/docs/ROBOT_SKU2.md).
- **SKU1:** both policies run on its ESP32 with the Mini Pupper v4 firmware, which loads the policy folders with its
  own tools: [the SKU1 robot guide](mp4_rl/skills/getup/docs/ROBOT_SKU1.md).

## What is where

```
mp4_rl/
  skills/          the bank: one folder per policy, registered in skills/__init__.py
    walker/          its page, code, recipes/, policies/, checkpoints/, eval/, media/
    getup/           the same, and docs/ (running both policies on each robot)
  common/          the policy interface (numpy), decoder bounds, export, PPO with the smoothness losses and the anchor,
                   the simulation environment on mp4_sim's scene, the classic gait baseline
  deploy/          the robot side: the runner and the serial link (numpy and pyserial only)
tools/             deploy, stop, lifted playback, calibration and joint limits for another unit, run summaries,
                   robot against simulation
scripts/install/   the installer and its checks
tests/             cpu/ needs no GPU, gpu/ 5-15 min
docs/              INSTALL, POLICY_CONTRACT, ADDING_A_POLICY
```

#!/bin/sh
# Fine-tune the get-up for the SKU1: resume the get-up's starting checkpoint on the SKU1's simulated plant, with the
# settings of the SKU2's get-up fine-tune (mp4_rl/skills/getup/recipes/sku2/finetune.sh) except the plant and the load on top.
# This recipe trained model_7543 (seed 71, 1000 iterations from model_6544), the parent of the shipped SKU1 get-up
# (mp4_rl/skills/getup/checkpoints/sku1/getup/model_8042.pt: 500 iterations more, seed 83, with the knee's reachable
# range at large thigh angles modelled in simulation, an option not in this repository yet).
#
#   sh mp4_rl/skills/getup/recipes/sku1/finetune.sh [SEED] [PARENT] [ITERS]
#
# SEED defaults to 71, PARENT to mp4_rl/skills/getup/checkpoints/sku2/getup_start/model_6544.pt,
# ITERS to 1000. Run from the repository root; output in runs/getup_sku1. Environment: PYTHON (default
# .venv/bin/python), ENVS (robots, default 1536), OUT (the output folder), EXTRA (more flags, appended last; argparse
# keeps the last value given).
#
# The settings:
# - starts: crouched, partly fallen, on a side, nose down, on the back and with random joints (5/5/25/15/40/10 %),
#   a fifth of the episodes from a mid-fall; 8 s episodes, a 4 s phase clock, an episode ends once the robot is up;
# - the action band 90/180/180 deg (abduction, hip, knee) inside the SKU1's joint limits traced on the robot, a target
#   filter of 0.75;
# - costs on the action rate and joint speed, the smoothness loss (`--caps-*`: temporal 2, spatial 40, observation noise 0.05);
# - terrain: half the columns flat, half rough ground (relief on a 2 cm grid, slopes, boxes) and the printed four- and
#   eight-step stairs (four columns each);
# - the SKU1's lidar (35 mm high, radius 19 mm, 47.2 g with its mount) on half the robots, its axis drawn 20 mm behind
#   to 10 mm in front of the base origin and 10 mm either side; the whole robot's centre of mass drawn 61-70 mm above
#   the floor (the weighed robot: 65.9 mm);
# - plant: the SKU1 (--robot sku1: its model, calibration, joint limits and weighed masses sku1_masses_413g.json), its
#   display as a collision box on the body (--display-collision), the MD-300 servo model with a 3S supply
#   (10.5-12.6 V) and winding resistance x0.95-1.15;
# - PPO: learning rate 1e-5 to at most 5e-5, the critic warmed up for 30 iterations; the policy's std is the checkpoint's
#   own (0.03; --init-std only sets a fresh actor's), clamped to 0.06-0.3 when sampling.
#
# The training is not bit-reproducible on a GPU: a new run gives a get-up of its own, to be evaluated before use
# (mp4_rl/skills/getup/README.md).
set -eu
SEED=${1:-71}
PARENT=${2:-mp4_rl/skills/getup/checkpoints/sku2/getup_start/model_6544.pt}
ITERS=${3:-1000}
# shellcheck disable=SC2086
exec env -u PYTHONPATH PYTHONPATH="$PWD" WANDB_MODE=disabled MUJOCO_GL=egl "${PYTHON:-.venv/bin/python}" -B \
  -m mp4_rl.skills.getup.train \
  --resume "$PARENT" --limits --getup-phase 4 --getup-band 90 180 180 --getup-episode-s 8 \
  --init-std 0.03 --entropy-coef 0 --getup-success-gyro 0 --getup-end-on-success --getup-midfall 0.2 \
  --getup-mix 0.05 0.05 0.25 0.15 0.40 0.10 0.05 0.05 0.25 0.15 0.40 0.10 \
  --actor-hidden 512 256 128 --critic-hidden 512 256 128 --obs-norm --obs-norm-freeze 100 \
  --lr0 1e-5 --lr-max 5e-5 --critic-warmup 30 \
  --getup-action-rate=-0.1 --getup-action-rate-tilted 1.0 --getup-joint-vel=-5e-4 \
  --getup-filter 0.75 --getup-filter-start 0.75 --getup-filter-ramp 0 \
  --caps-temporal 2 --caps-spatial 40 --caps-obs-noise 0.05 \
  --getup-terrain --relief-pitch 0.02 --getup-terrain-stairs 4 --std-bounds 0.06 0.3 \
  --getup-attachment --getup-attachment-height 35 35 --getup-attachment-mass 47.2 47.2 --getup-attachment-radius 19 \
  --getup-attachment-x -20 10 --getup-attachment-y -10 10 --getup-attachment-present 0.5 --com-height-mm 61 70 \
  --robot sku1 --masses-json sku1_masses_413g.json --display-collision \
  --actuator md300 --supply-v 10.5 12.6 --r-scale 0.95 1.15 \
  --envs "${ENVS:-1536}" --iters "$ITERS" --seed "$SEED" --out "${OUT:-runs/getup_sku1}" --tag getup_sku1 ${EXTRA:-}

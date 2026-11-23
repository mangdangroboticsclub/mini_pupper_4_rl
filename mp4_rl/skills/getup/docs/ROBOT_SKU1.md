# The walker and the get-up on the Mini Pupper v4 (SKU1)

The Mini Pupper v4 SKU1 is the short body on the SKU2's legs, servos and ESP32 board, without a Raspberry Pi. Both
policies run on the ESP32, at 50 Hz, with the
[Mini Pupper v4 firmware](https://github.com/mangdangroboticsclub/minipupper_4_mcu). The **walker**
(`mp4_rl/skills/walker/policies/sku1`) stands, walks in every direction, turns in place and rides out shoves. When the
firmware detects a fall it hands over to the **get-up** (`mp4_rl/skills/getup/policies/sku1`), which puts the robot back
on its feet; once the robot is upright, the walker takes over again.

## Requirements

- Mini Pupper v4 (SKU1), calibrated: the policy folders carry the calibration they were exported for
  (`sku1_contract.json`) and its joint limits (`sku1_joint_limits.json`); the robot's offsets have to match it (see
  [Another unit](#another-unit)).
- The Mini Pupper v4 firmware on the ESP32, built and flashed as its README describes. Load the policy folders with the
  firmware's tools: `mp4_rl/skills/walker/policies/sku1` and `mp4_rl/skills/getup/policies/sku1`.
- The get-up needs the firmware's knee-target limit at large thigh angles.
- A hand ready on the stop, a foam mat for floor falls, and a stand to put the robot on between runs.

## Safety

- **Abduction gears:** the servo module's abduction gear train is the robot's weak part. Feel the abductions by hand for
  new play or roughness after back flips and after each set of shoves, and stop if one feels rough. Keep a spare servo
  module on the bench.
- **Between runs, lift the robot onto its stand and let the servos cool:** standing on the floor between runs heats
  them.
- **Hands off, and the robot still, at the start of every run:** the gyro's bias is measured then, and a run in which the
  robot moved is refused. Stop a run before you pick the robot up.
- **Never command joints near the potentiometer track ends.** The policies' bounds keep every target at least 20° inside
  on the hips and knees; keep your own motions inside the same margins.
- Start a new policy with a lifted run (the robot on a block, every leg free) before the floor.

## What was measured

The get-up in `mp4_rl/skills/getup/policies/sku1` has not run on the robot yet, and it needs the firmware's knee-target
limit; the get-up rows below were measured with the previous get-up.

With `mp4_rl/skills/walker/policies/sku1` and the previous get-up on the robot's ESP32; each take is one run. Get-up
times come from the firmware's get-up log, speeds from the distance on a tape measure over the run's time, turn rates
from the angle turned over the run's time.

| | Takes | Result |
|---|---|---|
| Get-ups from placed fall poses: left side, right side, back, nose down | one per pose: 4 | every one up: right side 1.5 s, nose down 1.5 s, back 1.7 s, left side 3.9 s |
| Shoves by hand until it fell: standing, and walking forward at 0.10 m/s | 18 falls in 2 runs: 8 standing, 10 walking | 18 of 18 back up (standing: 1.5-1.8 s, one 6.6 s), and walking again in the walking run |
| Walking forward (0.10, 0.20 m/s), backward (0.10), left (0.10) and right (0.12) | 5 | 0.64-0.85 × the speed simulation predicts for the same command, no falls |
| Turning in place at +1.0, -1.0 and +2.0 rad/s | 3 | 0.64-0.79 × the simulated turn rate; up to 1.36 rad/s at a +2.0 rad/s command |
| Walking at 0.10 m/s while turning at -0.5 rad/s | 1 | 0.73 × the simulated speed, 0.61 × the simulated turn |

Per command:

| Command | Robot | Simulation | Robot / simulation |
|---|---|---|---|
| Forward 0.10 m/s | 0.076 m/s | 0.109 m/s | 0.70 |
| Forward 0.20 m/s | 0.133 m/s | 0.186 m/s | 0.72 |
| Backward 0.10 m/s | 0.075 m/s | 0.099 m/s | 0.76 |
| Left 0.10 m/s | 0.070 m/s | 0.109 m/s | 0.64 |
| Right 0.12 m/s | 0.102 m/s | 0.120 m/s | 0.85 |
| Turn +1.0 rad/s | 0.79 rad/s | 1.22 rad/s | 0.64 |
| Turn -1.0 rad/s | -0.98 rad/s | -1.25 rad/s | 0.79 |
| Turn +2.0 rad/s | 1.36 rad/s | 2.13 rad/s | 0.64 |
| Forward 0.10 m/s, turn -0.5 rad/s | 0.081 m/s along its arc, turn -0.25 rad/s | 0.112 m/s, turn -0.41 rad/s | 0.73 (speed), 0.61 (turn) |

The simulated figures are the walker's omni evaluation on the SKU1's plant (`mp4_rl/skills/walker/eval/sku1.sh`,
`omni_s21`). The lidar cases, the printed stairs and rough ground were evaluated in simulation.

## Another unit

The shipped calibration and joint limits are those of the unit the policies were trained for and measured on. Another
SKU1 needs a calibration file of its own: `tools/make_contract.py` writes one from the robot's calibration offsets and
stand (the file it reads is described in its `--help`), starting from the shipped one. Then re-export both policies for
it; the networks don't change, and each folder carries the new calibration:

```sh
.venv/bin/python tools/make_contract.py offsets.json --note "unit 2" --out my_robot/sku1_contract.json \
    --base mp4_rl/skills/walker/policies/sku1/sku1_contract.json
.venv/bin/python -m mp4_rl.common.export --from-policy mp4_rl/skills/walker/policies/sku1 my_robot/walker \
    --robot sku1 --contract my_robot/sku1_contract.json
.venv/bin/python -m mp4_rl.common.export --from-policy mp4_rl/skills/getup/policies/sku1 my_robot/getup \
    --robot sku1 --contract my_robot/sku1_contract.json
```

Where the stand moved far along a joint's track, the new bounds can cut motions the policy learned: compare them with the
old ones in each `policy.npz`'s meta, and retrain or re-horn the joint if a range shrank a lot. The SKU2 guide's
[Adapting to another unit](ROBOT_SKU2.md#adapting-to-another-unit) explains the joint limits and how to check them.

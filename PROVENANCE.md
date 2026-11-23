# Provenance

What the shipped files are and where they came from.

| File | What it is | sha256 |
|---|---|---|
| `mp4_rl/skills/walker/policies/sku2/policy.npz` | The walker that ran on the robot: `mp4_rl/skills/walker/checkpoints/sku2/walker/model_10793.pt` exported (`mp4_rl.common.export`), the abductions' stand 12° wider, then copied with `--from-policy` for the published calibration file (the network unchanged) | `5f7f2d70864c377c87aef3ae7546ed9def5c7deac862e21b22644c6a083372dd` |
| `mp4_rl/skills/getup/policies/sku2/policy.npz` | The get-up that ran on the robot: `mp4_rl/skills/getup/checkpoints/sku2/getup/model_7543.pt` exported, then copied with `--from-policy` for the published calibration file (the network unchanged) | `6b537110f8924d66a648882b2ddc24b065a39450b718c9731f1ab57b91be5c6d` |
| `mp4_rl/skills/walker/checkpoints/sku2/walker_start/model_6297.pt` | The walker's starting checkpoint: it descends from an earlier stair-climbing walker, trained on an older model of the robot in [mini_pupper_4_sim](https://github.com/mangdangroboticsclub/mini_pupper_4_sim), then trained further on rough ground and stairs | `33cc59eb3bf1c7384dea50263c719b522cae5bece5997fcf87acbf879f42c4ca` |
| `mp4_rl/skills/walker/checkpoints/sku2/walker/model_10793.pt` | The walker's final checkpoint: `recipes/sku2/step1.sh` to `step4.sh` from the starting checkpoint (seeds 71, 81, 91, 101) | `290793f29f483421b0504a752cfdf4fb7b461ad37fbd0b48882f6ea9affd2712` |
| `mp4_rl/skills/getup/checkpoints/sku2/getup_start/model_6544.pt` | The get-up's starting checkpoint: a get-up trained with the earlier servo model fit (`md01`) and an earlier mass estimate of the robot, with a load on the hood and uneven ground | `690dd19d9e627e224d07bd581dae399c79b7e94afaf274d128bed8aa889f6c99` |
| `mp4_rl/skills/getup/checkpoints/sku2/getup/model_7543.pt` | The get-up's final checkpoint: `recipes/sku2/finetune.sh` from the starting checkpoint (seed 72) | `2ebb10d46af9561ee684a13362a5febf3afc734eba9cfa94abfc22e223f9ddc7` |
| `mp4_rl/skills/*/policies/sku2/sku2_contract.json`, `sku2_joint_limits.json` | Byte copies of the SKU2's calibration and joint limits from mini_pupper_4_sim 0.2.0 (`robot/assets/sku_2/measured/`), the files each policy was exported for | `86f1d330a9f30d7e…`, `9cad8e76f4b8bf50…` |
| `mp4_rl/skills/walker/policies/sku1/policy.npz` | The SKU1 walker that ran on the robot: `mp4_rl/skills/walker/checkpoints/sku1/walker/model_11792.pt` exported for the SKU1 (`mp4_rl.common.export --robot sku1`), the abductions' stand 12° wider | `0168c007d4c7a6d56495d64725cecdbade39dd18c31929f65952094a6727a492` |
| `mp4_rl/skills/getup/policies/sku1/policy.npz` | The SKU1 get-up: `mp4_rl/skills/getup/checkpoints/sku1/getup/model_8042.pt` exported for the SKU1 | `ee2872b2e07aa7fd0d80578e61aee6aa18215079a7d9807ba3b8f480725c9417` |
| `mp4_rl/skills/walker/checkpoints/sku1/walker/model_11792.pt` | The SKU1 walker's final checkpoint: `recipes/sku1/finetune.sh` from the SKU2 walker's final checkpoint (`checkpoints/sku2/walker/model_10793.pt`), seed 210, 1000 iterations; the run used the walk-mode joint limits estimated before the SKU1's legs were traced (the SKU2's measured ranges at the SKU1's calibration), where the recipe uses the traced limits | `b715fa03d141b467e7a3157e4e294248d1d9f4631ca652eb3aa0f8c94a786fac` |
| `mp4_rl/skills/getup/checkpoints/sku1/getup/model_8042.pt` | The SKU1 get-up's final checkpoint: 500 iterations (seed 83) from model_7543, which `recipes/sku1/finetune.sh` trained from the get-up's starting checkpoint (`checkpoints/sku2/getup_start/model_6544.pt`, seed 71, 1000 iterations); trained with the knee's reachable range at large thigh angles modelled in simulation, an option not in this repository yet | `9acd1c2e194f6883464a0e8e58fb181fe675af379caf697c781cf3440149b8c5` |
| `mp4_rl/skills/*/policies/sku1/sku1_contract.json`, `sku1_joint_limits.json` | Byte copies of the SKU1's calibration and joint limits from mini_pupper_4_sim 0.2.0 (`robot/assets/sku_1/measured/`), the files each SKU1 policy was exported for | `48720bbdd8828779…`, `8b1274d545b5cb9f…` |

The two starting checkpoints are given as they are: they are where the recipes begin, and their own training can't be
reproduced from this repository. The SKU1 recipes (`mp4_rl/skills/*/recipes/sku1/`) start from the SKU2 checkpoints above. A
recipe run again gives a policy of its own (training on a GPU is not bit-reproducible, and the result depends on the
seed); the shipped checkpoints are the runs whose policies ran on the robots.

Each checkpoint's `config.json` holds only the run options that `--resume` and `mp4_rl.common.export` read. Each policy's
meta records its checkpoint's sha256 (`checkpoint_sha256`), the calibration's (`contract_sha256`), the joint limits'
(`bounds.info.limits_sha256`), the robot model's (`legs.model_sha256`), and `source_policy_sha256`, which
`mp4_rl.common.export --from-policy` records: the hash of the policy file the weights were copied from. Each policy's
`config.json` holds its training run's options and names the robot model, masses, joint limits and servo parameters
it was trained on by their names in mini_pupper_4_sim (`mp4_sim:...`) and their sha256; the SKU1 walker's names the
traced joint limits it is exported for (above).

## Data

| File | What it is |
|---|---|
| `mp4_rl/skills/getup/data/sku2_proven_reach.json` | How far each hip has moved towards the body's middle on the robot, per abduction bin (the 99.5th percentile, from at least 20 samples): summarised from 28 runs on the SKU2 (809.5 s); the logs are not part of this repository. `mp4_rl.skills.getup.eval.reach` compares a simulated get-up with it |
| `tests/cpu/data/feedback_glitches.npz` | Two excerpts of a SKU2 run log: a limp leg moved by hand with ten frames of impossible position readings, and a still stretch |
| `tests/cpu/data/sku2_imu_captures.npz` | Accelerometer captures from the SKU2 while trotting |
| `tests/cpu/data/firmware_trot_ticks.npz` | The firmware's trot (its gait and inverse kinematics, built on the host) tabulated at several speeds for one calibration |
| `tests/cpu/data/sku2_contract_test.json` | A calibration file with other offsets than the shipped one |
| `tests/data/compare_run/` | Small run and stream logs in the robot's log formats, for the tests of `tools/compare_run.py` |
| `tests/data/phase_restart_cross.json` | Scripted get-up cases played through the runner on a simulated board: the reference the GPU sequence test compares with |

The robot model, its measured data, the fitted servo parameters and the servo model code come from mini_pupper_4_sim;
the servo model builds on [BAM](https://github.com/Rhoban/bam). The masses were weighed and the joint limits measured by
hand on the robots the policies ran on.

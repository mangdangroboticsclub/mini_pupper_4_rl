"""The shipped policies and checkpoints, SKU2 and SKU1: arrays and files pinned, the numpy forward pass against their
fixtures, metadata free of local paths, the policies what ``common.export`` writes from the shipped checkpoints (arrays
and the whole meta), the calibration and limits copies in each folder, the recipes' command lines."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from mp4_sim import limits as sim_limits
from mp4_sim import robots as sim_robots

from mp4_rl import paths
from mp4_rl.common.policy import CONTRACT_JSON, Bounds
from mp4_rl.common.policy_file import NumpyPolicy, fixture_tolerance
from mp4_rl.deploy.runner import runner as rn

REPO = Path(__file__).resolve().parents[2]
ARRAYS = {
    ("walker", "sku2"): "e301f53fa9cd1985b7984c78b0ed37313d742ca519922b358692965d85ae5efa",
    ("getup", "sku2"): "c1eb8ab20780a51e9e9cc19bb54ddd0f3eb1482dbc04103968b2d0ce9a806e00",
    ("walker", "sku1"): "1fda4e6b55cf37c49219e8a74fe25492e05a4236d5a8b38fa686a90798179cd4",
    ("getup", "sku1"): "42d4381c0165c6a6a91265241238fc6e8b90f3cdf2c37ff0b367de7a3d087857",
}
# the policy files' bytes (they are never written again: a re-export must reproduce the arrays and the meta)
NPZ = {
    ("walker", "sku2"): "5f7f2d70864c377c87aef3ae7546ed9def5c7deac862e21b22644c6a083372dd",
    ("getup", "sku2"): "6b537110f8924d66a648882b2ddc24b065a39450b718c9731f1ab57b91be5c6d",
    ("walker", "sku1"): "0168c007d4c7a6d56495d64725cecdbade39dd18c31929f65952094a6727a492",
    ("getup", "sku1"): "ee2872b2e07aa7fd0d80578e61aee6aa18215079a7d9807ba3b8f480725c9417",
}
POLICIES = list(ARRAYS)
FINAL = {("walker", "sku2"): "sku2/walker/model_10793.pt", ("getup", "sku2"): "sku2/getup/model_7543.pt",
         ("walker", "sku1"): "sku1/walker/model_11792.pt", ("getup", "sku1"): "sku1/getup/model_8042.pt"}
# each policy's final checkpoint, and the checkpoints the recipes start from, by (skill, path in its checkpoints/):
# (iteration, an observation normaliser) and sha256
CHECKPOINTS = {("walker", "sku2/walker/model_10793.pt"): (10793, False), ("getup", "sku2/getup/model_7543.pt"): (7543, True),
               ("walker", "sku2/walker_start/model_6297.pt"): (6297, False),
               ("getup", "sku2/getup_start/model_6544.pt"): (6544, True),
               ("walker", "sku1/walker/model_11792.pt"): (11792, False), ("getup", "sku1/getup/model_8042.pt"): (8042, True)}
SHA = {("walker", "sku2/walker/model_10793.pt"): "290793f29f483421b0504a752cfdf4fb7b461ad37fbd0b48882f6ea9affd2712",
       ("getup", "sku2/getup/model_7543.pt"): "2ebb10d46af9561ee684a13362a5febf3afc734eba9cfa94abfc22e223f9ddc7",
       ("walker", "sku2/walker_start/model_6297.pt"): "33cc59eb3bf1c7384dea50263c719b522cae5bece5997fcf87acbf879f42c4ca",
       ("getup", "sku2/getup_start/model_6544.pt"): "690dd19d9e627e224d07bd581dae399c79b7e94afaf274d128bed8aa889f6c99",
       ("walker", "sku1/walker/model_11792.pt"): "b715fa03d141b467e7a3157e4e294248d1d9f4631ca652eb3aa0f8c94a786fac",
       ("getup", "sku1/getup/model_8042.pt"): "9acd1c2e194f6883464a0e8e58fb181fe675af379caf697c781cf3440149b8c5"}


def ids(p) -> str:
    return "-".join(p)


def policy_dir(name: str, robot: str = "sku2") -> Path:
    return REPO / "mp4_rl" / "skills" / name / "policies" / robot


def checkpoint(skill: str, rel: str) -> Path:
    return REPO / "mp4_rl" / "skills" / skill / "checkpoints" / rel


def robot_files(robot: str):
    r = sim_robots.get(robot)
    return r.contract_json, r.limits_json
LOCAL = ("/home", "/tmp", "wandb", "runs/")


def arrays_sha256(path) -> str:
    h = hashlib.sha256()
    with np.load(path, allow_pickle=False) as d:
        for k in sorted(d.files):
            if k != "meta":
                h.update(k.encode())
                h.update(d[k].tobytes())
    return h.hexdigest()


def same_meta(made: dict, shipped: dict) -> None:
    for k in set(made) | set(shipped):
        if k != "source_policy_sha256":
            assert made.get(k) == shipped.get(k), k


@pytest.mark.parametrize("name, robot", POLICIES, ids=ids)
def test_arrays_and_fixtures(name, robot):
    path = policy_dir(name, robot) / "policy.npz"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == NPZ[name, robot]
    assert arrays_sha256(path) == ARRAYS[name, robot]
    p = NumpyPolicy(path)
    d = np.load(path, allow_pickle=False)
    assert np.abs(p(d["fixture_obs"]) - d["fixture_act"]).max() < fixture_tolerance(d["fixture_act"])


@pytest.mark.parametrize("name, robot", POLICIES, ids=ids)
def test_meta_and_config(name, robot):
    meta = NumpyPolicy(policy_dir(name, robot) / "policy.npz").meta
    r = sim_robots.get(robot)
    assert meta["contract_sha256"] == paths.sha256(r.contract_json)
    assert meta["checkpoint_sha256"] == paths.sha256(checkpoint(name, FINAL[name, robot])) == SHA[name, FINAL[name, robot]]
    assert meta["bounds"]["info"]["limits_sha256"] == paths.sha256(r.limits_json)
    assert meta["legs"]["model_sha256"] == paths.sha256(r.xml)
    if robot == "sku2":
        assert meta["contract_sha256"] == paths.sha256(CONTRACT_JSON)
        assert meta["bounds"]["info"]["limits_sha256"] == sim_limits.LIMITS_SHA256
        assert "robot" not in meta
    else:
        assert meta["robot"] == meta["legs"]["robot"] == robot
    Bounds.from_meta(meta["bounds"])
    for text in (json.dumps(meta), (policy_dir(name, robot) / "config.json").read_text()):
        assert not any(s in text for s in LOCAL), text[:200]


@pytest.mark.parametrize("name, robot", POLICIES, ids=ids)
def test_each_folder_carries_byte_copies_of_the_calibration_and_the_limits(name, robot):
    for f in robot_files(robot):
        assert (policy_dir(name, robot) / f.name).read_bytes() == f.read_bytes()
    assert sorted(p.name for p in policy_dir(name, robot).iterdir()) == [
        "config.json", "policy.npz", f"{robot}_contract.json", f"{robot}_joint_limits.json"]


@pytest.mark.parametrize("name, robot", POLICIES, ids=ids)
def test_the_configs_name_the_simulation_files_and_their_hashes(name, robot):
    """config.json names the robot's files as mp4_sim names, with the hashes of mp4_sim's files."""
    from mp4_sim import paths as sim_paths
    cfg = json.loads((policy_dir(name, robot) / "config.json").read_text())["task"]
    assert cfg["options"].get("robot", "sku2") == robot and cfg["legs"].get("robot", "sku2") == robot
    assert cfg["limits"]["limits_json"] == sim_paths.name(sim_robots.get(robot).limits_json)
    names = list(cfg["sources"]) + [r["params"] for r in cfg["servo_params"]["roles"].values()] + \
        [cfg["limits"]["limits_json"]]
    assert len(names) == 7 and all(n.startswith("mp4_sim:") for n in names)
    for n, sha in cfg["sources"].items():
        assert sim_paths.sha256(sim_paths.resolve(n)) == sha, n
    for r in cfg["servo_params"]["roles"].values():
        assert sim_paths.sha256(sim_paths.resolve(r["params"])) == r["sha256"]


@pytest.mark.parametrize("name", ["walker", "getup"])
def test_runner_check_passes(name):
    assert rn.main(["check", "--policy", str(policy_dir(name))]) == 0


def test_the_get_up_holds_the_packaged_hip_envelope():
    from mp4_rl.common import bounds as limits
    meta = NumpyPolicy(policy_dir("getup") / "policy.npz").meta
    assert meta["bounds"]["hip_envelope"] == limits.hip_envelope()


def test_the_get_up_stops_the_front_right_hip_at_its_limit():
    """No thigh stop: at straight abduction the FR thigh's backward side is open (the track clamp acts), and where the
    hip envelope caps it (a traced chassis contact) the target stops there."""
    from mp4_rl.common.policy import Contract
    c = Contract.load()
    st = c.stand_rel_rad
    b = Bounds.from_meta(NumpyPolicy(policy_dir("getup") / "policy.npz").meta["bounds"])
    e = b.hip_envelope["FR"]
    rel = np.zeros(12)
    rel[1] = np.radians(90.0)                          # the model's + is backward on this thigh
    assert np.interp(st[0], e["abd"], e["hi"]) >= 10.0 - 1e-9                       # open at the stand's abduction
    assert b.clamp_rel(rel, st)[1] == pytest.approx(b.hi[1] - st[1], abs=1e-12)     # the track clamp
    capped = [(a, h) for a, h in zip(e["abd"], e["hi"]) if h < 10.0 and b.lo[0] <= a <= b.hi[0]]
    assert capped                                       # some columns are capped at a traced contact
    for a, h in capped:
        rel[0] = a - st[0]
        assert b.clamp_rel(rel, st)[1] == pytest.approx(min(h, b.hi[1]) - st[1], abs=1e-9), np.degrees(a)


def export(*args):
    import mp4_sim
    src = os.pathsep.join([str(REPO), str(Path(mp4_sim.__file__).resolve().parents[1])])
    subprocess.run([sys.executable, "-m", "mp4_rl.common.export", *map(str, args)], check=True, cwd=REPO,
                   env={"PYTHONPATH": src, "PATH": "/usr/bin:/bin", "WANDB_MODE": "disabled"})


@pytest.mark.parametrize("name, robot", POLICIES, ids=ids)
def test_export_from_policy_keeps_arrays_and_meta(tmp_path, name, robot):
    out = tmp_path / name
    export("--from-policy", policy_dir(name, robot), out)
    assert arrays_sha256(out / "policy.npz") == ARRAYS[name, robot]
    made, shipped = (NumpyPolicy(p / "policy.npz").meta for p in (out, policy_dir(name, robot)))
    assert str(tmp_path) not in json.dumps(made) and str(REPO) not in json.dumps(made)
    same_meta(made, shipped)
    assert made["source_policy_sha256"] == NPZ[name, robot]
    for f in ("config.json", f"{robot}_contract.json", f"{robot}_joint_limits.json"):
        assert (out / f).read_bytes() == (policy_dir(name, robot) / f).read_bytes(), f


@pytest.mark.parametrize("name, robot", POLICIES, ids=ids)
def test_the_final_checkpoints_export_to_the_shipped_policies(tmp_path, name, robot):
    out = tmp_path / name
    export(checkpoint(name, FINAL[name, robot]), out)
    assert arrays_sha256(out / "policy.npz") == ARRAYS[name, robot]
    same_meta(NumpyPolicy(out / "policy.npz").meta, NumpyPolicy(policy_dir(name, robot) / "policy.npz").meta)
    if robot == "sku1":       # exported from the checkpoint as shipped: the same bytes
        assert hashlib.sha256((out / "policy.npz").read_bytes()).hexdigest() == NPZ[name, robot]
    for f in (f"{robot}_contract.json", f"{robot}_joint_limits.json"):
        assert (out / f).read_bytes() == (policy_dir(name, robot) / f).read_bytes(), f


@pytest.mark.parametrize("name", ["walker", "getup"])
def test_the_sku1_configs_hold_the_options_their_recipes_build(tmp_path, name):
    """The SKU1 policy's config.json options are what its recipe's command line builds, from the recipe's parent."""
    pytest.importorskip("mjlab")
    from dataclasses import asdict, is_dataclass
    rel = f"mp4_rl/skills/{name}/recipes/sku1/finetune.sh"
    rc, _, err = recipe(tmp_path, rel, OUT=str(tmp_path / "out"), ANCHOR="x/anchor")
    assert rc == 0, err
    argv = (tmp_path / "args").read_text().split()
    if name == "walker":
        from mp4_rl.skills.walker import train as tw
        a = tw.build_parser().parse_args(argv[argv.index("mp4_rl.skills.walker.train") + 1:])
        src = json.loads((REPO / a.resume).with_name("config.json").read_text())["task"]["options"]
        o = tw.walker_options(a, src, tw.resume_step(REPO / a.resume))
    else:
        from mp4_rl.skills.getup import train as tg
        a = tg.parse_args(argv[argv.index("mp4_rl.skills.getup.train") + 1:])
        o = tg.task_options(a)
    assert paths.sha256(REPO / a.resume) == SHA[name, {"walker": "sku2/walker/model_10793.pt",
                                                       "getup": "sku2/getup_start/model_6544.pt"}[name]]
    built = json.loads(json.dumps({k: asdict(v) if is_dataclass(v) else v for k, v in o.__dict__.items()}))
    assert built == json.loads((policy_dir(name, "sku1") / "config.json").read_text())["task"]["options"]
    assert (a.seed, a.iters) == ({"walker": 210, "getup": 71}[name], 1000)


def test_checkpoints_load_as_plain_tensors_with_their_options():
    import torch
    for (skill, name), (it, norm) in CHECKPOINTS.items():
        assert paths.sha256(checkpoint(skill, name)) == SHA[skill, name], name
        ck = torch.load(checkpoint(skill, name), map_location="cpu", weights_only=True)
        assert ck.get("iter") == it and ck["critic_state_dict"] and ck["optimizer_state_dict"]
        assert ("obs_normalizer._mean" in ck["actor_state_dict"]) == norm
        cfg = checkpoint(skill, name).parent / "config.json"
        o = json.loads(cfg.read_text())["task"]["options"]
        assert len(o["action_scale"]) == 12 and o["kind"] in ("walk", "getup")
        assert not any(s in cfg.read_text() for s in LOCAL)


def recipe(tmp_path, name, *args, cwd=REPO, **env):
    """Run a recipe with a ``python`` that records its arguments; returns (exit code, the arguments as a dict, stderr)."""
    stub = tmp_path / "python"
    stub.write_text(f'#!/bin/sh\necho "$@" > {tmp_path / "args"}\n')
    stub.chmod(0o755)
    r = subprocess.run(["sh", str(REPO / name), *args], cwd=cwd, capture_output=True, text=True,
                       env={"PYTHON": str(stub), "PATH": "/usr/bin:/bin", **env})
    a = (tmp_path / "args").read_text().split() if (tmp_path / "args").exists() else []
    opts = {}
    for i, x in enumerate(a):
        if x.startswith("--"):
            opts[x] = a[i + 1] if i + 1 < len(a) and not a[i + 1].startswith("--") else True
    return r.returncode, opts, r.stderr


@pytest.mark.parametrize("name, seed, iters, start, anchor", [
    ("mp4_rl/skills/walker/recipes/sku2/step1.sh", "71", "1000", "mp4_rl/skills/walker/checkpoints/sku2/walker_start/model_6297.pt", "mp4_rl/skills/walker/checkpoints/sku2/walker_start/model_6297.pt"),
    ("mp4_rl/skills/getup/recipes/sku2/finetune.sh", "72", "1000", "mp4_rl/skills/getup/checkpoints/sku2/getup_start/model_6544.pt", None),
])
def test_recipes_start_from_the_shipped_checkpoints(tmp_path, name, seed, iters, start, anchor):
    rc, o, err = recipe(tmp_path, name)
    assert rc == 0, err
    assert (o["--seed"], o["--iters"], o["--resume"], o.get("--anchor")) == (seed, iters, start, anchor)
    assert (REPO / start).is_file() and (REPO / start).with_name("config.json").is_file()
    assert o["--actuator"] == "md300" and "--masses-json" not in o and "--legs" not in o      # the packaged robot


def test_recipe_settings_and_overrides(tmp_path):
    rc, o, _ = recipe(tmp_path, "mp4_rl/skills/walker/recipes/sku2/step1.sh", "5", "my/parent.pt", "2", ENVS="64", OUT="runs/smoke")
    assert rc == 0 and (o["--seed"], o["--resume"], o["--anchor"], o["--iters"]) == ("5", "my/parent.pt", "my/parent.pt", "2")
    assert (o["--envs"], o["--out"], o["--cmd-ramp"], o["--save-at"]) == ("64", "runs/smoke", "300", "300")
    rc, o, _ = recipe(tmp_path, "mp4_rl/skills/getup/recipes/sku2/finetune.sh", ENVS="64")
    assert rc == 0 and o["--envs"] == "64" and o["--std-bounds"] == "0.06" and o["--getup-attachment"] is True


@pytest.mark.parametrize("script, name, flag, full, quick", [
    ("mp4_rl/skills/getup/eval/sku2.sh", "gflat_s21", "--robots", "512", "64"),
    ("mp4_rl/skills/getup/eval/sku1.sh", "gterr_s21", "--robots", "1024", "128"),
    ("mp4_rl/skills/walker/eval/sku2.sh", "omni_s21", "--per", "24", "3"),
    ("mp4_rl/skills/walker/eval/sku1.sh", "push_s21", "--robots", None, "8"),
    ("mp4_rl/skills/walker/eval/sku2.sh", "wstairs_s21", "--envs", "256", "32"),
])
def test_quick_evaluations_run_an_eighth_of_the_robots(tmp_path, script, name, flag, full, quick):
    for env, want in (({}, full), ({"QUICK": "1"}, quick)):
        rc, o, err = recipe(tmp_path, script, str(tmp_path / f"out{len(env)}"), name, WALKER="w", GETUP="g", **env)
        assert rc == 0 and o.get(flag) == want, (env, o, err)


@pytest.mark.parametrize("n, seed, iters", [(2, "81", "1500"), (3, "91", "1000"), (4, "101", "1000")])
def test_later_walker_steps_continue_from_the_step_before(tmp_path, n, seed, iters):
    work = tmp_path / "w"
    rc, _, err = recipe(tmp_path, f"mp4_rl/skills/walker/recipes/sku2/step{n}.sh", cwd=work.mkdir() or work)
    assert rc == 2 and f"no run in runs/walker_step{n - 1}" in err
    run = work / f"runs/walker_step{n - 1}/20270101_000000_s1_step{n - 1}"
    run.mkdir(parents=True)
    for k in (7050, 7297, 7100):
        (run / f"model_{k}.pt").touch()
    rc, o, err = recipe(tmp_path, f"mp4_rl/skills/walker/recipes/sku2/step{n}.sh", cwd=work)
    assert rc == 0, err
    assert (o["--seed"], o["--iters"], o["--tag"]) == (seed, iters, f"step{n}")
    assert o["--resume"] == f"runs/walker_step{n - 1}/{run.name}/model_7297.pt"
    assert o["--anchor"] == "mp4_rl/skills/walker/checkpoints/sku2/walker_start/model_6297.pt" and o["--cmd-ramp"] == "0"


def test_the_install_check_covers_both_robots_policies(tmp_path, monkeypatch):
    import importlib.util
    spec = importlib.util.spec_from_file_location("verify", REPO / "scripts/install/verify.py")
    verify = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verify)
    assert sorted(verify.policy_hashes()) == [("getup sku1", None), ("getup sku2", None), ("walker sku1", None),
                                              ("walker sku2", None)]
    import shutil

    from mp4_rl import skills
    for name, robot in POLICIES:
        shutil.copytree(policy_dir(name, robot), tmp_path / name / "policies" / robot)
    c = tmp_path / "walker/policies/sku1/sku1_contract.json"
    c.write_text(c.read_text() + " ")                 # one byte more: no longer mp4_sim's file
    monkeypatch.setattr(skills, "HERE", tmp_path)
    got = dict(verify.policy_hashes())
    assert got["walker sku1"] == "the folder's sku1_contract.json" and got["getup sku1"] is None

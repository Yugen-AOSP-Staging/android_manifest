# Project Yugen — manifest 幽玄

`repo` manifest for **Project Yugen**, an AOSP 17 distribution that boots on
LineageOS device trees.

```bash
repo init -u https://github.com/Yugen-AOSP-Staging/android_manifest -b reimi
repo sync -j4 --no-clone-bundle --no-tags
```

AOSP's git server rate-limits anonymous clones. If you see `HTTP 429` /
`expected 'acknowledgments'` on `android.googlesource.com` projects, drop to
`-j2` and rerun the same command: `repo sync` resumes, it does not restart.
Do not raise `-j` there; the limit is per IP, so more jobs make it worse.

Only the LineageOS projects can fail permanently. [`tools/check-branches.py`](#validating)
checks their pins without a sync.

## How it is built

Yugen is **not** a LineageOS fork. `default.xml` is the unmodified AOSP manifest
for `android-17.0.0_r1`, plus five includes:

| Snippet | Purpose |
|---|---|
| `snippets/remote.xml` | remotes: yugen, lineage, github, gitlab |
| `snippets/remove.xml` | drop AOSP emulator/reference devices and any path we replace |
| `snippets/external.xml` | LineageOS **hardware glue** — `hardware/qcom-caf`, `vendor/qcom/opensource`, extract tools, `devicesettings`. No platform forks. |
| `snippets/custom.xml` | `vendor/yugen` + `vendor/lineage` compat shim |
| `snippets/devices.xml` | per-device repositories (empty in v1) |

The platform is 100% AOSP: `build/make`, `art`, `bionic`, `frameworks/base`,
`system/sepolicy` all come from `android.googlesource.com` at
`android-17.0.0_r1`. LineageOS supplies only the HAL/vendor layer that Qualcomm
device trees need.

## Adding a device

1. Confirm the tree exists: `git ls-remote --heads https://github.com/LineageOS/android_device_<vendor>_<codename> lineage-24.0`
2. Add its `device/`, `kernel/` and `vendor/` projects to `snippets/devices.xml`.
3. `repo sync --local-only` (or full sync), then:

```bash
source build/envsetup.sh
lunch lineage_<codename>-userdebug
m
```

The product name stays `lineage_<codename>` because that is what the device tree
declares; Yugen identity is applied at runtime through `vendor/yugen`.

## Regenerating the AOSP base

```bash
./tools/gen-manifest.sh android-17.0.0_r1
```

This re-fetches AOSP's `default.xml`, re-appends the includes, fixes the `aosp`
remote to an absolute URL, and then validates the merged manifest.

## Validating

```bash
./tools/validate.py        # offline: structure, duplicates, remotes, removals
./tools/check-branches.py  # network: every pinned branch exists upstream
```

`validate.py` resolves includes and `remove-project` entries in `repo` order.
`check-branches.py` is the one that would have caught a stale pin before a sync:
it asks GitHub for the heads of every snippet project and suggests the newest
`lineage-*` branch when the pinned one is gone.

### Branch pins

Most snippet projects take the `lineage-24.0` default from
`snippets/remote.xml`, but SoC-specific HALs are pinned per entry. Two rules:

- Keep the per-entry `revision=` when the same repository is used at several
  `hardware/qcom-caf/<soc>/` paths — each path needs its own branch.
- Do not add legacy non-CAF `hardware/qcom/{camera,display,gps,media,bt}` or
  `data/ipacfg-mgr` globally. Their newest branches are `lineage-22.2`/`23.0`
  and they would poison every sync. Declare them per device in
  `snippets/devices.xml`, with the branch the device tree expects.

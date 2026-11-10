# Project Yugen — manifest 幽玄

`repo` manifest for **Project Yugen**, an AOSP 17 distribution that boots on
LineageOS device trees.

```bash
repo init -u https://github.com/Yugen-AOSP-Staging/android_manifest -b reimi
repo sync -j"$(nproc)" --no-clone-bundle --no-tags
```

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
./tools/validate.py
```

Checks every snippet is well formed, that no project path or name is declared
twice, and that every `remote=` resolves.

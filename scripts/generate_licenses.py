"""从当前环境生成 THIRD_PARTY_NOTICES.md，列出项目依赖及其许可证。

用法：
    python scripts/generate_licenses.py

会读取 requirements.txt 中的直接依赖，并通过 importlib.metadata 递归收集
传递依赖，最终在仓库根目录生成 THIRD_PARTY_NOTICES.md。
"""

from __future__ import annotations

import re
from importlib import metadata as md
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "requirements.txt"
OUTPUT = ROOT / "THIRD_PARTY_NOTICES.md"

# 某些发行包的元数据缺少 License 字段，这里按官方声明手动补齐。
KNOWN_LICENSES = {
    "pdfplumber": "MIT",
    "loguru": "MIT",
}


def read_direct_dependencies() -> list[str]:
    deps: list[str] = []
    for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        deps.append(_package_name(line))
    return deps


def _package_name(requirement: str) -> str:
    """把 'pandas>=2.2.0' 之类的行解析为包名 'pandas'。"""
    name = requirement.split(";", 1)[0].strip()
    name = name.split("[", 1)[0]
    return re.split(r"[<>=!~ ]", name, maxsplit=1)[0].strip()


def _classifier_license(dist: md.Distribution) -> str | None:
    for classifier in dist.metadata.get_all("Classifier") or []:
        if classifier.startswith("License :: OSI Approved ::"):
            return classifier.removeprefix("License :: OSI Approved ::").strip()
    return None


def resolve_license(dist: md.Distribution, key: str) -> str:
    expression = dist.metadata.get("License-Expression")
    if expression:
        return expression
    classifier = _classifier_license(dist)
    if classifier:
        return classifier
    if key in KNOWN_LICENSES:
        return KNOWN_LICENSES[key]
    license_field = dist.metadata.get("License")
    if license_field and license_field.strip() and license_field.strip().lower() != "unknown":
        return license_field.strip().splitlines()[0][:80]
    return "UNKNOWN"


def collect(direct: list[str]) -> dict[str, tuple[str, str, str]]:
    found: dict[str, tuple[str, str, str]] = {}
    queue = list(direct)
    while queue:
        name = queue.pop(0)
        try:
            dist = md.distribution(name)
        except md.PackageNotFoundError:
            continue
        key = dist.metadata["Name"].lower().replace("_", "-")
        if key in found:
            continue
        found[key] = (dist.metadata["Name"], dist.version, resolve_license(dist, key))
        for requirement in dist.requires or []:
            if "extra ==" in requirement:
                continue  # 可选 extra（如 test/dev），非默认安装，跳过
            dep = _package_name(requirement)
            dep_key = dep.lower().replace("_", "-")
            if dep and dep_key not in found and dep_key not in queue:
                queue.append(dep)
    return found


def main() -> int:
    direct = read_direct_dependencies()
    found = collect(direct)
    direct_keys = {d.lower().replace("_", "-") for d in direct}
    ordered = sorted(found.items(), key=lambda kv: (kv[0] not in direct_keys, kv[0]))

    lines = [
        "# Third-Party Notices",
        "",
        "本项目使用以下第三方开源组件。各组件许可证的完整文本保留在其上游仓库与分发包中。",
        "分发本项目（包括打包后的可执行文件）时，请保留本文件，以满足各许可证对版权声明的保留要求。",
        "",
        "> 注意：`PyMuPDF` 采用 AGPL-3.0 或 Artifex 商业授权（双许可）。本项目以开源方式分发；",
        "> 若要进行闭源商业分发，需联系 Artifex 获取商业授权，或替换该组件。",
        "",
        "| 组件 | 版本 | 许可证 |",
        "|------|------|--------|",
    ]
    for key, (display, version, license_text) in ordered:
        lines.append(f"| {display} | {version} | {license_text.replace('|', '\\|')} |")

    lines.extend(
        [
            "",
            "## 许可证说明",
            "",
            "- **PyMuPDF (fitz)**：AGPL-3.0 或 Artifex 商业授权（双许可）。开源分发可满足 AGPL 义务；闭源商业化前需替换或购买商业授权。",
            "- 其余组件均为宽松许可证（MIT / BSD / Apache-2.0 / MPL-2.0），在保留版权声明的前提下可自由使用、修改与分发。",
            "",
            f"*本文件由 `scripts/generate_licenses.py` 自动生成，共 {len(found)} 个组件。*",
        ]
    )

    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"已生成：{OUTPUT}")
    print(f"共 {len(found)} 个第三方组件")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

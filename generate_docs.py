"""Generate README.md and CHEATSHEET.md from pme_preset.json.

Usage: python generate_docs.py
更新预设后重新运行即可重写两份文档。
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent
data = json.loads((ROOT / "pme_preset.json").read_text(encoding="utf-8"))
menus = {m[0]: m for m in data["menus"]}

ITEM_TYPES = {"COMMAND", "MENU", "PROP", "OP", "MACRO"}

CTX = {
    "3D View": "3D 视图", "Object Mode": "物体模式", "Mesh": "网格编辑",
    "Curve": "曲线", "Curves": "Curves", "Lattice": "晶格", "UV Editor": "UV 编辑器",
    "Weight Paint": "权重绘制", "Pose": "姿态", "Node Generic": "节点",
    "Sculpt": "雕刻", "Outliner": "大纲", "Animation": "动画",
    "Window": "全局", "File Browser": "文件浏览器",
}

GROUPS = {
    "物体": "物体模式", "网格": "网格编辑", "曲线": "曲线", "晶格": "晶格",
    "UV": "UV 编辑器", "权重": "权重绘制", "姿态": "姿态", "节点": "节点",
    "雕刻": "雕刻", "大纲": "大纲", "动画": "动画", "相机": "相机",
    "切换编辑器": "界面切换", "分流": "分流脚本", "Alt+D": "Alt+D 系列",
    "Alt+E": "Alt+E 系列", "旋转": "旋转", "备份": "备份",
    "幽灵显示": "特殊功能", "狙击手模式": "特殊功能",
}
OTHER = "其他 / 辅助弹窗"


def group_of(name):
    first = name.split(" ")[0]
    for prefix, label in GROUPS.items():
        if first.startswith(prefix):
            return label
    return OTHER


def trans_ctx(s):
    return " / ".join(CTX.get(t.strip(), t.strip()) for t in s.split(";") if t.strip())


def expand_items(menu_name, depth=0, seen=None):
    """递归展开菜单条目，返回 [(缩进, 标签, 是否子菜单)]"""
    if seen is None:
        seen = set()
    m = menus.get(menu_name)
    if not m or depth > 3 or menu_name in seen:
        return []
    seen = seen | {menu_name}
    rows = []
    for it in m[3]:
        if len(it) < 3 or it[1] not in ITEM_TYPES:
            continue
        label, typ = it[0], it[1]
        if typ == "MENU":
            target = (it[3] or label).lstrip("@") if len(it) > 3 else label
            rows.append((depth, label, True))
            rows.extend(expand_items(target, depth + 1, seen))
        else:
            rows.append((depth, label, False))
    return rows


# ---------- 分组 ----------
grouped = {}
for name in menus:
    grouped.setdefault(group_of(name), []).append(name)

order = [label for label in GROUPS.values() if label in grouped] + (
    [OTHER] if OTHER in grouped else []
)

# ---------- CHEATSHEET.md ----------
lines = [
    "# 菜单速查表",
    "",
    f"> 自动生成自 `pme_preset.json`（PME {data.get('version')}），共 {len(menus)} 个菜单。",
    "子菜单以嵌套列表展开；名称中的「点击 / 长按 / 拖动 / 单击」即触发方式。",
    "",
]
for label in order:
    names = sorted(grouped[label])
    lines.append(f"## {label}（{len(names)}）")
    lines.append("")
    for name in names:
        m = menus[name]
        ctx = trans_ctx(m[1]) if len(m) > 1 else ""
        mtype = m[4] if len(m) > 4 else ""
        lines.append(f"### {name}")
        if ctx:
            lines.append(f"*适用：{ctx}*")
        lines.append("")
        rows = expand_items(name)
        if not rows:
            lines.append("（无固定条目 / 动态生成）")
            lines.append("")
            continue
        for depth, lbl, is_menu in rows:
            lines.append("  " * depth + f"- {lbl}" + ("（子菜单）" if is_menu else ""))
        lines.append("")
(ROOT / "CHEATSHEET.md").write_text("\n".join(lines), encoding="utf-8")

# ---------- README.md ----------
total_items = sum(1 for m in menus.values() for it in m[3] if len(it) > 2 and it[1] in ITEM_TYPES)
n_modes = len(order)

readme = [
    "# PME 饼菜单预设 (Pie Menu Editor Preset)",
    "",
    "一套深度定制的 Blender 全模式饼菜单配置："
    f"**{len(menus)} 个菜单、弹窗与脚本、约 {total_items} 个功能条目**，"
    "覆盖物体、网格、曲线、晶格、UV、权重绘制、姿态、节点、雕刻等模式；"
    "常用键 D / W / F / A / S / V / E / R / X 按「点击 / 长按 / 拖动」分派不同菜单。",
    "",
    "> 本仓库只包含配置预设。**需要自购并安装 "
    "[Pie Menu Editor](https://blendermarket.com/products/pie-menu-editor) "
    f"{data.get('version')} 及以上版本**才能使用。",
    "",
    "## 导入",
    "",
    "1. 在 [Releases](../../releases) 下载 `pme_preset.json`（或直接使用仓库文件）",
    "2. 打开 PME 界面，使用其 **Import（导入）** 功能选择该 json 文件"
    "（不同版本入口名称略有差异，可参考 PME 文档的 Import/Export 部分）",
    "3. 导入后如个别命令提示缺失，多为面向个人工作流的插件调用或宏，"
    "可在 PME 中删除或替换，不影响其余菜单",
    "",
    "## 键位总览",
    "",
    f"按编辑模式共分 {n_modes} 组：",
    "",
    "| 分组 | 数量 | 菜单 |",
    "| --- | --- | --- |",
]
for label in order:
    names = sorted(grouped[label])
    readme.append(f"| {label} | {len(names)} | {'、'.join(names)} |")
readme += [
    "",
    "每个菜单的完整条目见 **[CHEATSHEET.md](CHEATSHEET.md)**（全部展开，自动生成）。",
    "",
    "## 说明",
    "",
    "- 菜单名中的「点击 / 长按 / 拖动 / 单击」对应 PME 的触发方式（同键可绑定不同菜单）",
    "- 适合作为底稿：导入后按自己的习惯增删条目、调整键位",
    "",
    "---",
    "",
    "整理：一枫 · License: [CC-BY-4.0](LICENSE)",
]
(ROOT / "README.md").write_text("\n".join(readme), encoding="utf-8")

print(f"README.md + CHEATSHEET.md generated | menus={len(menus)} items={total_items} groups={n_modes}")

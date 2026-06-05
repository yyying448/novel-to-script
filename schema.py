"""
YAML Schema 定义与校验

本模块定义了剧本的 YAML 数据结构（Schema），并提供校验函数。
Schema 的设计原因详见项目根目录下的 SCHEMA.md 文档。
"""

from typing import List, Dict, Any, Tuple


# ============================================================
# Schema 定义（以注释 + 示例结构展示）
# ============================================================

SCRIPT_SCHEMA_EXAMPLE = {
    "meta": {
        "title": "小说原名",
        "author": "原作者",
        "adapted_from": "第1章 少年出走",
        "script_version": 1,
        "generated_at": "2026-06-05T12:00:00"
    },
    "scenes": [
        {
            "scene_id": 1,
            "location": "内景 - 城主府大殿 - 日",
            "characters_present": [
                {"name": "林风", "role": "主角"},
                {"name": "侍女小翠", "role": "配角"}
            ],
            "summary": "林风首次进入城主府，与侍女发生争执",
            "dialogues": [
                {
                    "speaker": "侍女小翠",
                    "lines": [
                        "站住！城主府岂是你随便进的地方？"
                    ],
                    "tone": "严厉，带着傲慢",
                    "action": "伸手拦住林风的去路"
                },
                {
                    "speaker": "林风",
                    "lines": [
                        "我找城主有事，麻烦通报一声。"
                    ],
                    "tone": "平静但坚定",
                    "action": "停下脚步，平静地直视侍女"
                }
            ],
            "scene_notes": "开场冲突场景，建立主角沉着性格，同时暗示城主府森严的等级制度"
        }
    ]
}


# ============================================================
# 字段说明（供前端"查看 Schema"功能使用）
# ============================================================

FIELD_DESCRIPTIONS = {
    "meta": "剧本元信息，记录来源、版本等追溯信息",
    "meta.title": "原著小说名称",
    "meta.author": "原著作者",
    "meta.adapted_from": "改编来源（章节信息）",
    "meta.script_version": "剧本版本号，每次修改递增",
    "meta.generated_at": "生成时间戳",
    "scenes": "场景列表，按剧情时间线排列",
    "scenes[].scene_id": "场景序号，从1开始递增",
    "scenes[].location": "场景空间描述，格式：内景/外景 - 具体地点 - 时间（日/夜/黄昏/清晨）",
    "scenes[].characters_present": "本场景出场人物列表",
    "scenes[].characters_present[].name": "角色名称",
    "scenes[].characters_present[].role": "角色类型：主角/重要配角/配角/龙套",
    "scenes[].summary": "本场景一句话概括（建议20字以内）",
    "scenes[].dialogues": "本场景所有对话列表",
    "scenes[].dialogues[].speaker": "说话人名称",
    "scenes[].dialogues[].lines": "台词行数组（同一人连续说多句话时放在一起）",
    "scenes[].dialogues[].tone": "语气描述（如：平静/愤怒/温柔/讽刺/紧张）",
    "scenes[].dialogues[].action": "说话同时进行的动作、表情或走位",
    "scenes[].scene_notes": "编剧备注：本场景的戏剧功能、情绪基调、伏笔等"
}


# ============================================================
# 校验函数
# ============================================================

def validate_script(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    校验生成的剧本数据是否符合 Schema

    Args:
        data: 解析后的剧本字典

    Returns:
        (是否通过校验, 错误信息列表)
    """
    errors = []

    # 检查顶层结构
    if not isinstance(data, dict):
        return False, ["剧本数据必须是字典/对象"]

    if "scenes" not in data:
        errors.append("缺少顶层字段 'scenes'")
        return False, errors

    scenes = data.get("scenes", [])
    if not isinstance(scenes, list):
        errors.append("'scenes' 必须是列表")
        return False, errors

    if len(scenes) == 0:
        errors.append("'scenes' 不能为空（至少需要一个场景）")
        return False, errors

    # 检查每个场景
    required_scene_fields = ["scene_id", "location", "summary"]
    required_dialogue_fields = ["speaker", "lines"]

    for i, scene in enumerate(scenes):
        prefix = f"scenes[{i}]"

        # 检查必填字段
        for field in required_scene_fields:
            if field not in scene:
                errors.append(f"{prefix}.{field} 缺失")

        # 检查 location 格式
        if "location" in scene and scene["location"]:
            loc = scene["location"]
            if " - " not in loc:
                errors.append(
                    f"{prefix}.location 格式不正确，应为 '内景/外景 - 地点 - 时间'，"
                    f"当前值: '{loc}'"
                )

        # 检查对话
        dialogues = scene.get("dialogues", [])
        if not isinstance(dialogues, list):
            errors.append(f"{prefix}.dialogues 必须是列表")
            continue

        for j, dialogue in enumerate(dialogues):
            d_prefix = f"{prefix}.dialogues[{j}]"

            for field in required_dialogue_fields:
                if field not in dialogue:
                    errors.append(f"{d_prefix}.{field} 缺失")

            if "lines" in dialogue:
                if not isinstance(dialogue["lines"], list):
                    errors.append(f"{d_prefix}.lines 必须是数组")
                elif len(dialogue["lines"]) == 0:
                    errors.append(f"{d_prefix}.lines 不能为空数组")

    return len(errors) == 0, errors


def get_schema_markdown() -> str:
    """
    生成 Schema 的 Markdown 格式说明（供前端"查看 Schema"弹窗使用）
    """
    md = """## YAML Schema 结构说明

```yaml
meta:                          # 剧本元信息（可选但建议保留）
  title: "小说名"              # 原著名称
  author: "作者"               # 原著作者
  adapted_from: "章节信息"     # 改编来源
  script_version: 1            # 版本号
  generated_at: "时间戳"       # 生成时间

scenes:                        # 场景列表（必填，至少1个）
  - scene_id: 1                # 场景序号
    location: "内景 - 地点 - 日"  # 场景时空（格式：内外景 - 地点 - 时间）
    characters_present:        # 出场人物
      - name: "角色名"
        role: "主角/配角/龙套"
    summary: "场景概括"        # 一句话描述
    dialogues:                 # 对话列表
      - speaker: "说话人"
        lines:                 # 台词（数组，支持多句连说）
          - "第一句"
          - "第二句"
        tone: "语气"           # 表演指导
        action: "动作"         # 同步动作
    scene_notes: "编剧备注"    # 戏剧功能说明
```

### 字段要求

| 字段 | 必填 | 说明 |
|------|:----:|------|
| scenes | ✅ | 顶层，至少包含1个场景 |
| scene_id | ✅ | 从1递增 |
| location | ✅ | 格式：`内景/外景 - 地点 - 时间` |
| summary | ✅ | 20字以内概括 |
| speaker | ✅ | 说话人名称 |
| lines | ✅ | 台词数组，至少1句 |
| tone | 推荐 | 帮助演员理解语气 |
| action | 推荐 | 帮助演员理解动作 |
| scene_notes | 推荐 | 帮助编剧理解场景意图 |
"""
    return md

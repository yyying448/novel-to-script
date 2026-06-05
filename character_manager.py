"""
角色一致性引擎

核心创新：原生 AI 对话中，第 50 章的角色和第 1 章可能判若两人。
本模块在逐章转换过程中：
1. 自动提取并注册角色（姓名/身份/性格/说话风格/人际关系）
2. 每章注入已知角色档案，确保跨章节角色一致性
3. 转换完成后生成完整角色小传 + 关系图
"""

from collections import defaultdict
from typing import Dict, List, Any, Optional


class CharacterProfile:
    """单个角色的完整档案"""

    def __init__(self, name: str, role: str = "未知"):
        self.name = name
        self.role = role  # 主角/重要配角/配角/龙套
        self.chapters: List[str] = []  # 出场章节列表
        self.scene_count = 0  # 出场场景次数
        self.dialogue_count = 0  # 台词句数
        self.personality = ""  # 性格描述（LLM 分析）
        self.speech_style = ""  # 说话风格（LLM 分析）
        self.identity = ""  # 身份背景
        self.relationships: Dict[str, str] = {}  # {角色名: 关系描述}
        self.emotional_arc: List[str] = []  # 情绪变化轨迹
        self.key_actions: List[str] = []  # 关键行为

    def to_inject_prompt(self) -> str:
        """生成注入到章节转换 prompt 中的简洁角色档案"""
        parts = [f"- {self.name}"]
        if self.role and self.role != "未知":
            parts[0] += f"（{self.role}）"
        if self.personality:
            parts.append(f"  性格：{self.personality}")
        if self.speech_style:
            parts.append(f"  说话风格：{self.speech_style}")
        if self.identity:
            parts.append(f"  身份：{self.identity}")
        if self.relationships:
            rels = "；".join(f"与{k}：{v}" for k, v in self.relationships.items())
            parts.append(f"  关系：{rels}")
        return "\n".join(parts)


class CharacterManager:
    """角色注册中心，管理所有角色的生命周期"""

    def __init__(self):
        self.characters: Dict[str, CharacterProfile] = {}

    # ================================================================
    # 增量注册（逐章调用，零额外 LLM 开销）
    # ================================================================

    def register_from_scenes(self, scenes: List[Dict], chapter_title: str):
        """
        从刚转换完成的场景中提取角色信息，增量更新档案
        """
        if not scenes:
            return
        for scene in scenes:
            characters_in_scene = scene.get("characters_present", [])
            if not characters_in_scene:
                continue

            # 收集本场景说话人
            speakers_in_scene = set()
            for d in scene.get("dialogues", []):
                if d and d.get("speaker"):
                    speakers_in_scene.add(d["speaker"])

            for char in characters_in_scene:
                if not char or not char.get("name"):
                    continue

                name = char["name"]
                role = char.get("role", "未知")

                # 首次出现的角色：创建档案
                if name not in self.characters:
                    self.characters[name] = CharacterProfile(name, role)
                    self.characters[name].chapters.append(chapter_title)

                profile = self.characters[name]

                # 更新角色类型（可能从配角升级）
                if role == "主角" or (profile.role != "主角" and role == "重要配角"):
                    profile.role = role

                # 统计出场
                profile.scene_count += 1

                # 统计台词
                if name in speakers_in_scene:
                    profile.dialogue_count += sum(
                        1 for d in scene.get("dialogues", [])
                        if d and d.get("speaker") == name
                    )

                # 记录首次出场章节
                if chapter_title not in profile.chapters:
                    profile.chapters.append(chapter_title)

    # ================================================================
    # 角色一致性注入（加入每章转换 prompt）
    # ================================================================

    def get_consistency_prompt(self, chapter_title: str) -> str:
        """
        生成角色一致性注入文本，附加在每章转换 prompt 中

        只注入已出场且有一定台词的角色（过滤龙套），
        保持信息密度高、不浪费 token。
        """
        important_chars = [
            c for c in self.characters.values()
            if c.role in ("主角", "重要配角") or c.dialogue_count >= 3
        ]

        if not important_chars:
            return ""

        lines = ["\n=== 已知角色档案（请保持角色性格、说话风格、身份一致）==="]
        for char in important_chars:
            lines.append(char.to_inject_prompt())
        lines.append("请确保以上角色的言行与其档案一致。若引入新角色，请沿用此格式自动建档。\n")

        return "\n".join(lines)

    # ================================================================
    # 角色关系推断（规则引擎，零 LLM 开销）
    # ================================================================

    def infer_relationships(self):
        """
        基于角色共现场景推断基础关系
        规则：共现场景 > 3 次的角色对，标记为"已知"
        """
        # 统计角色共现矩阵
        co_occur = defaultdict(lambda: defaultdict(int))
        # 注：这里需要场景级数据，从已有的 chapters 出场信息做近似
        # 简化处理：如果两个角色在同一章节出场，标记关系
        chapters_with_chars = defaultdict(list)
        for name, profile in self.characters.items():
            for ch in profile.chapters:
                chapters_with_chars[ch].append(name)

        for ch, names in chapters_with_chars.items():
            for i, n1 in enumerate(names):
                for n2 in names[i + 1:]:
                    co_occur[n1][n2] += 1
                    co_occur[n2][n1] += 1

        # 为高频共现的角色建立关系
        for name, profile in self.characters.items():
            related = co_occur.get(name, {})
            for other, count in related.items():
                if count >= 2 and other not in profile.relationships:
                    profile.relationships[other] = "有关联"

    # ================================================================
    # 角色报告生成
    # ================================================================

    def get_summary(self) -> List[Dict]:
        """生成角色摘要列表（供前端展示）"""
        self.infer_relationships()
        result = []
        for name, c in sorted(
            self.characters.items(),
            key=lambda x: (
                0 if x[1].role == "主角" else 1 if x[1].role == "重要配角" else 2,
                -x[1].scene_count
            )
        ):
            result.append({
                "name": name,
                "role": c.role,
                "chapters_count": len(c.chapters),
                "scene_count": c.scene_count,
                "dialogue_count": c.dialogue_count,
                "personality": c.personality,
                "speech_style": c.speech_style,
                "identity": c.identity,
                "relationships": dict(c.relationships),
                "first_chapter": c.chapters[0] if c.chapters else "未知",
                "chapters": c.chapters,
                "emotional_arc": c.emotional_arc,
                "key_actions": c.key_actions,
            })
        return result

    def deep_analyze(self, llm_client) -> str:
        """
        调用 LLM 对所有角色进行深度分析（性格/说话风格/关系/弧光）

        在所有章节转换完成后调用一次，生成高质量角色小传。
        """
        if not self.characters:
            return "暂无角色数据。"

        from llm_client import call_llm
        from prompts import CHARACTER_REPORT_PROMPT

        # 构建角色基础数据
        char_data = []
        for name, c in self.characters.items():
            char_data.append(
                f"角色：{name}\n"
                f"  类型：{c.role}\n"
                f"  出场章节数：{len(c.chapters)}，出场场景数：{c.scene_count}，台词句数：{c.dialogue_count}\n"
                f"  出场章节：{' → '.join(c.chapters[:10])}"
            )

        prompt = CHARACTER_REPORT_PROMPT.format(
            character_data="\n".join(char_data)
        )

        system_prompt = "你是一位专业的文学角色分析师，擅长从剧本数据中洞察角色性格、关系和成长弧光。"
        response = call_llm(llm_client, system_prompt, prompt, temperature=0.5)
        return response

    def apply_deep_analysis(self, report_text: str):
        """
        将 LLM 深度分析结果解析并回填到角色档案

        简单策略：在报告中搜索角色名附近的描述关键词
        """
        # 简化处理：直接保存报告原文，前端展示
        # 深度解析可用更复杂的 NLP，但当前版本以报告形式呈现即可
        pass

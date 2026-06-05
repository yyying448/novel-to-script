"""
改编智能体（Adaptation Agent）

核心竞争力：AI 原生对话只会"直译"，不懂剧本行业规则。
本模块提供：
1. 改编策略报告 —— 哪些保留/压缩/删除/合并
2. 不可拍内容识别 —— 内心独白→旁白、抽象描写→具象场景
3. 场景时长估算 —— 每场戏预估分钟数 + 全剧总时长
4. 拍摄难度标签 —— 群戏/VFX/外景/夜戏/动作/特技
5. 导演概览 —— 每场戏的戏剧功能与情绪基调

创新点：从"翻译"升级为"改编顾问"，这是专业编剧才有的能力。
"""

import re
from typing import List, Dict, Any, Optional, Tuple


# ================================================================
# 拍摄难度关键词词典
# ================================================================

DIFFICULTY_PATTERNS = {
    "群戏": [
        r"(群|众|多|数|几十|上百|成千|一众|人们|人群|众人|满堂|满座|齐聚|云集)",
        r"characters_present.{0,50}(?:\d{2,}|[6-9]|[1-9]\d)",
    ],
    "外景": [r"(外景|野外|山林|沙漠|海边|雪山|草原|街道|马路|广场|码头)"],
    "夜戏": [r"(夜|晚|黄昏|暮|暗|月光|星|灯|火把|烛)"],
    "VFX特效": [
        r"(魔法|法术|飞天|变身|幻化|消失|闪现|光柱|爆炸|火焰|雷电|冰霜|结界|传送)",
        r"(monster|dragon|beast|magic|spell|transform)",
    ],
    "动作场面": [
        r"(打斗|搏斗|刺杀|追击|奔跑|跳跃|翻墙|骑马|射箭|挥剑|出拳|踢|摔|格斗|战斗|厮杀)",
        r"(fight|chase|run|jump|climb|attack)",
    ],
    "特技/威亚": [r"(飞檐走壁|轻功|吊|钢丝|威亚|空翻|倒吊|悬浮|腾空)"],
    "水下/雨戏": [r"(水下|潜水|雨|暴雨|淋雨|湿透|水底|湖|河|淹|溺)"],
    "情绪重场": [r"(哭|崩溃|嘶吼|歇斯底里|泪|绝望|崩溃大哭|嚎啕|撕心裂肺)"],
    "代唱/配乐关键": [r"(唱|歌|琴|曲|箫|笛|鼓|弹奏|吟|咏)"],
}


# 不可拍内容识别
UNFILMABLE_PATTERNS = [
    (r"(心想|心中暗想|内心独白|心里想|暗忖|思忖|默默想着|心头涌起)",
     "💡 内心独白 → 建议改为旁白(VO)或通过表情/动作外化"),
    (r"(回忆起|记忆中|回想|想起|脑海里浮现|往事浮现)",
     "💡 回忆闪回 → 标注为 FLASHBACK，注意转场方式"),
    (r"(仿佛|好像|似乎|如同|像是|宛若|宛如)",
     "⚠️ 抽象比喻 → 需导演可视化，建议标注视觉参考"),
    (r"(感觉|觉得|感到|感受到|莫名|不由得|情不自禁)",
     "⚠️ 主观感受 → 建议转化为具体动作或表情"),
    (r"(无尽的|无限的|漫天的|铺天盖地的|浩瀚的|磅礴的)",
     "🎬 宏大形容词 → 需在 scene_notes 中补充具象视觉方案"),
]


def analyze_scene_duration(scene: Dict) -> float:
    """
    估算单场戏时长（分钟）

    算法：
    - 每句台词 ≈ 0.1 分钟（含反应镜头）
    - scene_notes 长度 > 50 字 ≈ +0.5 分钟（说明有复杂调度）
    - 动作场面 × 1.5
    - 基础起步 0.5 分钟
    """
    base = 0.5

    # 台词时间
    dialogue_lines = 0
    for d in scene.get("dialogues", []):
        if d and d.get("lines"):
            lines = d["lines"]
            if isinstance(lines, list):
                dialogue_lines += len(lines)
    base += dialogue_lines * 0.1

    # 复杂调度加分
    notes = scene.get("scene_notes", "")
    if len(notes) > 50:
        base += 0.5

    # 动作场面加权
    action_text = ""
    for d in scene.get("dialogues", []):
        if d and d.get("action"):
            action_text += d["action"]
    if _match_any(action_text, DIFFICULTY_PATTERNS["动作场面"]):
        base *= 1.5

    return round(max(0.5, base), 1)


def tag_scene_difficulty(scene: Dict) -> List[str]:
    """
    为场景打拍摄难度标签

    检测项：群戏/外景/夜戏/VFX特效/动作场面/特技威亚/
           水下雨戏/情绪重场/代唱配乐
    """
    tags = []

    # 收集所有文本用于关键词匹配
    text = scene.get("location", "")
    text += " " + scene.get("summary", "")
    text += " " + scene.get("scene_notes", "")
    for d in scene.get("dialogues", []):
        if d:
            text += " " + (d.get("action") or "")

    # 额外检查：出场人物 ≥ 8 标注群戏
    chars = scene.get("characters_present", [])
    if len(chars) >= 8:
        tags.append("群戏")

    for tag, patterns in DIFFICULTY_PATTERNS.items():
        if tag == "群戏":
            continue  # 已用人数判断
        if _match_any(text, patterns):
            tags.append(tag)

    return tags


def detect_unfilmable(scene: Dict) -> List[str]:
    """
    识别场景中的"不可拍内容"并给出改编建议
    """
    warnings = []
    text = scene.get("summary", "") + " " + scene.get("scene_notes", "")
    for d in scene.get("dialogues", []):
        if d:
            text += " " + (d.get("action") or "")
            for line in (d.get("lines") or []):
                text += " " + (line or "")

    for pattern, advice in UNFILMABLE_PATTERNS:
        if re.search(pattern, text):
            warnings.append(advice)

    return list(set(warnings))  # 去重


def analyze_dramatic_function(scene: Dict, index: int, total: int) -> str:
    """
    推断场景的戏剧功能

    基于位置和内容简单推断（启发式规则）
    """
    position = "开场" if index == 0 else "结尾" if index == total - 1 else "中段"
    summary = scene.get("summary", "")
    notes = scene.get("scene_notes", "")

    # 关键词判断
    text = summary + notes
    if any(w in text for w in ["冲突", "争执", "打斗", "对决", "对峙", "争吵"]):
        return "冲突推进"
    if any(w in text for w in ["揭示", "真相", "发现", "秘密", "得知", "坦白"]):
        return "信息揭示"
    if any(w in text for w in ["情感", "表白", "相拥", "离别", "重逢", "哭泣"]):
        return "情感高潮"
    if any(w in text for w in ["计划", "商量", "决定", "商议", "谋划"]):
        return "决策/铺垫"
    if any(w in text for w in ["出发", "分别", "启程", "离开", "告别"]):
        return "转折/过渡"
    if position == "开场":
        return "建立/引入"
    if position == "结尾":
        return "收束/悬念"

    return "日常推进"


def estimate_total_runtime(scenes: List[Dict]) -> Tuple[float, float, float]:
    """
    估算全剧总时长

    Returns:
        (最小时长, 最可能时长, 最大时长)
    """
    if not scenes:
        return (0, 0, 0)

    durations = [analyze_scene_duration(s) for s in scenes]
    total = sum(durations)

    # 考虑转场时间（每场 +0.2 分钟）
    transitions = len(scenes) * 0.2

    most_likely = round(total + transitions, 1)
    min_est = round(most_likely * 0.8, 1)
    max_est = round(most_likely * 1.3, 1)

    return (min_est, most_likely, max_est)


def analyze_all_scenes(scenes: List[Dict]) -> List[Dict]:
    """
    对全部场景进行完整分析，结果附加到每个场景上
    """
    if not scenes:
        return []
    total = len(scenes)
    for i, scene in enumerate(scenes):
        scene["estimated_duration"] = analyze_scene_duration(scene)
        scene["difficulty_tags"] = tag_scene_difficulty(scene)
        scene["unfilmable_warnings"] = detect_unfilmable(scene)
        scene["dramatic_function"] = analyze_dramatic_function(scene, i, total)

    return scenes


def generate_adaptation_strategy(
    novel_preview: str,
    chapter_summary: List[Dict],
    llm_client,
    model: str = "deepseek-chat",
) -> str:
    """
    调用 LLM 生成改编策略报告
    """
    from llm_client import call_llm
    from prompts import ADAPTATION_STRATEGY_PROMPT

    # 构建章节摘要
    ch_info = "\n".join([
        f"- {ch.get('title', '?')}（{ch.get('char_count', 0)} 字）"
        for ch in chapter_summary
    ])

    prompt = ADAPTATION_STRATEGY_PROMPT.format(
        novel_preview=novel_preview[:5000],
        chapter_summary=ch_info
    )

    system = "你是一位剧本改编顾问，擅长分析小说结构并给出可操作的影视改编建议。回答简洁专业，不寒暄，不自我介绍，直接输出分析内容。"

    response = call_llm(llm_client, system, prompt, model=model, temperature=0.6, max_tokens=2048)
    return response


# ================================================================
# 分集拆分（按用户设定的单集时长，在章节边界智能切分）
# ================================================================

def split_into_episodes(
    scenes: List[Dict],
    target_minutes: float = 45.0,
    chapter_map: Optional[Dict[str, str]] = None,
) -> List[Dict]:
    """
    将场景列表按目标单集时长拆分为多集

    算法：
    1. 按顺序遍历场景，累加 estimated_duration
    2. 累计时长 >= target_minutes 时，向前找最近章节边界切分
    3. 不在场景中间切断（始终在章节边界或场景边界切）
    4. 为每集生成标题和一句话摘要

    Args:
        scenes: 已含 estimated_duration 的场景列表
        target_minutes: 目标单集时长（分钟），默认 45
        chapter_map: 章节标题 → 原文映射（可选）

    Returns:
        分集列表 [{episode_id, title, summary, scenes, estimated_duration}]
    """
    if not scenes:
        return []

    episodes = []
    current_ep_scenes = []
    current_duration = 0.0
    current_chapters = set()
    ep_id = 1

    for i, scene in enumerate(scenes):
        dur = scene.get("estimated_duration", 1.0)
        chapter = scene.get("chapter", "未知")

        # 检查是否该切分
        should_split = (
            current_duration + dur >= target_minutes
            and current_ep_scenes  # 至少有内容
            and chapter != current_ep_scenes[-1].get("chapter", "")  # 章节边界
        )

        # 如果当前集为空或离目标还远，继续累积
        if not should_split:
            current_ep_scenes.append(scene)
            current_duration += dur
            current_chapters.add(chapter)
        else:
            # 保存当前集
            episodes.append(_make_episode(ep_id, current_ep_scenes, current_chapters))
            ep_id += 1

            # 开始新集
            current_ep_scenes = [scene]
            current_duration = dur
            current_chapters = {chapter}

    # 最后一集
    if current_ep_scenes:
        episodes.append(_make_episode(ep_id, current_ep_scenes, current_chapters))

    return episodes


def _make_episode(ep_id: int, scenes: List[Dict], chapters: set) -> Dict:
    """构建单集对象"""
    total_dur = round(sum(s.get("estimated_duration", 1.0) for s in scenes), 1)
    ch_list = [c for c in scenes[0].get("chapter", "未知").split()[0:1]] if scenes else []

    # 生成标题
    if len(chapters) == 1:
        ch_name = list(chapters)[0]
        title = f"第{ep_id}集 · {ch_name}"
    else:
        first_ch = scenes[0].get("chapter", "?")
        last_ch = scenes[-1].get("chapter", "?")
        title = f"第{ep_id}集 · {first_ch} ~ {last_ch}"

    # 生成摘要（取首尾场景的 summary 拼接）
    first_summary = scenes[0].get("summary", "") if scenes else ""
    last_summary = scenes[-1].get("summary", "") if scenes else ""
    if first_summary and last_summary and first_summary != last_summary:
        summary = f"{first_summary} → {last_summary}"
    else:
        summary = first_summary or f"共 {len(scenes)} 场戏"

    return {
        "episode_id": ep_id,
        "title": title,
        "summary": summary,
        "scenes": scenes,
        "scene_count": len(scenes),
        "estimated_duration": total_dur,
    }


# ================================================================
# 工具函数
# ================================================================

def _match_any(text: str, patterns: List[str]) -> bool:
    """检查文本是否匹配任一正则模式"""
    for p in patterns:
        if re.search(p, text):
            return True
    return False

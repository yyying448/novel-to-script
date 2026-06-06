export interface Provider {
  key: string; name: string; model: string; help: string;
}

export interface Chapter {
  title: string; char_count: number; estimated_tokens: number;
}

export interface Character {
  name: string; role: string;
  chapters_count: number; scene_count: number; dialogue_count: number;
  personality: string; speech_style: string; identity: string;
  motivation: string; appearance: string;
  relationships: Record<string, string>;
  first_chapter: string; chapters: string[];
  emotional_arc: string[]; key_actions: string[];
}

export interface Dialogue {
  speaker: string; lines: string[]; tone: string; action: string;
}

export interface Scene {
  scene_id: number; chapter: string;
  location: string; summary: string; scene_notes: string;
  characters_present: { name: string; role: string }[];
  dialogues: Dialogue[];
  estimated_duration?: number;
  difficulty_tags?: string[];
  unfilmable_warnings?: string[];
  dramatic_function?: string;
  conflict_types?: string[];
  conflict_intensity?: number;
  conflict_description?: string;
}

export interface Episode {
  episode_id: number; title: string; summary: string;
  scenes: Scene[]; scene_count: number; estimated_duration: number;
}

export interface ScriptResult {
  scenes?: Scene[];
  characters?: Character[];
  episodes?: Episode[];
  runtime?: { min: number; likely: number; max: number };
  character_count?: number; episode_count?: number;
}

export interface ModelResult {
  label: string; scenes: Scene[]; characters: Character[];
  episodes: Episode[]; runtime: Record<string, number>;
  character_count: number; episode_count: number; error?: string;
}

export interface CompareResult {
  label: string; scene_count: number;
  score: any; error: string;
  preview: Scene[]; all_scenes: Scene[];
}

export interface SSEEvent {
  type: string; label?: string; idx?: number;
  report?: string; data?: Chapter[];
  count?: number; chapter_map?: Record<string, string>;
  current?: number; total?: number; title?: string;
  status?: string; percent?: number;
  scenes?: Scene[]; characters?: Character[];
  completed?: number;
  result?: ScriptResult; scene_count?: number;
  runtime?: any; episodes?: any[];
  chapter_count?: number; character_count?: number;
  strategy_report?: string; episode_count?: number;
  all_results?: ModelResult[];
  results?: CompareResult[];
  error?: string; message?: string;
}

export interface ConvertParams {
  text: string; api_key: string; provider: string;
  base_url?: string; model?: string;
  episode_minutes: number;
  compare_keys: string; compare_models: string; compare_providers: string;
}

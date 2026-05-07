/**
 * 旁白时间点标记组件
 */

export interface NarratorMark {
  time: number;
  text: string;
  section: string;
}

export function generateNarratorScript(marks: NarratorMark[]): string {
  return marks.map((m) => `[${formatTime(m.time)}] ${m.section}: ${m.text}`).join("\n");
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
}

export function buildNarratorMarks(
  sections: Array<{ id: string; startTime: number; narration: string }>
): NarratorMark[] {
  return sections.map((s) => ({ time: s.startTime, text: s.narration, section: s.id }));
}

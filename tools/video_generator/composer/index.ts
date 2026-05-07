/**
 * 主合成器：组装所有 14 个段落为完整视频合成
 */

import { ProjectData } from "./data-types";

import { openingConfig, generateOpeningHTML } from "./sections/opening";
import { stage01Config, generateStage01HTML } from "./sections/stage_01";
import { stage02Config, generateStage02HTML } from "./sections/stage_02";
import { stage03Config, generateStage03HTML } from "./sections/stage_03";
import { stage04Config, generateStage04HTML } from "./sections/stage_04";
import { stage05Config, generateStage05HTML } from "./sections/stage_05";
import { stage06Config, generateStage06HTML } from "./sections/stage_06";
import { stage07Config, generateStage07HTML } from "./sections/stage_07";
import { stage08Config, generateStage08HTML } from "./sections/stage_08";
import { stage09Config, generateStage09HTML } from "./sections/stage_09";
import { stage10Config, generateStage10HTML } from "./sections/stage_10";
import { stage11Config, generateStage11HTML } from "./sections/stage_11";
import { stage12Config, generateStage12HTML } from "./sections/stage_12";
import { stage13Config, generateStage13HTML } from "./sections/stage_13";

import { generateNarratorScript, buildNarratorMarks } from "./components/narrator-mark";

// 加载数据
import projectData from "./data/project_data.json" assert { type: "json" };
const data = projectData as ProjectData;

interface SectionDef {
  id: string;
  duration: number;
  skipIf?: (data: ProjectData) => boolean;
  generate: (data: ProjectData) => string;
  narration: string;
}

const sections: SectionDef[] = [
  { ...openingConfig, generate: generateOpeningHTML },
  { ...stage01Config, generate: generateStage01HTML },
  { ...stage02Config, generate: generateStage02HTML },
  { ...stage03Config, generate: generateStage03HTML },
  { ...stage04Config, generate: generateStage04HTML },
  { ...stage05Config, generate: generateStage05HTML },
  { ...stage06Config, generate: generateStage06HTML },
  { ...stage07Config, generate: generateStage07HTML },
  { ...stage08Config, generate: generateStage08HTML },
  { ...stage09Config, generate: generateStage09HTML },
  { ...stage10Config, generate: generateStage10HTML },
  { ...stage11Config, generate: generateStage11HTML },
  { ...stage12Config, generate: generateStage12HTML },
  { ...stage13Config, generate: generateStage13HTML },
];

function buildComposition(): { html: string; narratorScript: string } {
  let currentTime = 0;
  const activeSections: Array<{ id: string; startTime: number; narration: string; html: string }> = [];

  for (const section of sections) {
    if (section.skipIf?.(data)) {
      console.log(`跳过 ${section.id}（数据不可用）`);
      continue;
    }
    activeSections.push({
      id: section.id,
      startTime: currentTime,
      narration: section.narration,
      html: section.generate(data),
    });
    currentTime += section.duration;
  }

  const narratorMarks = buildNarratorMarks(activeSections);
  const narratorScript = generateNarratorScript(narratorMarks);
  const html = activeSections.map((s) => s.html).join("\n\n<!-- SECTION BREAK -->\n\n");

  return { html, narratorScript };
}

const { html, narratorScript } = buildComposition();

console.log(`有效段落数：${sections.filter((s) => !s.skipIf?.(data)).length}`);
console.log(`总时长：${sections.reduce((sum, s) => sum + (s.skipIf?.(data) ? 0 : s.duration), 0)}秒`);
console.log(`\n旁白脚本：\n${narratorScript}`);

export default html;

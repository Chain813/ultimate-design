/** 视频生成数据类型定义 */

export interface ProjectData {
  project: {
    name: string;
    subtitle: string;
    location: string;
    area: string;
  };
  stages: Record<string, StageData>;
  narrator_marks: NarratorMark[];
}

export interface StageData {
  title: string;
  data: Record<string, any>;
  images: Record<string, string>;
  skip?: boolean;
}

export interface NarratorMark {
  time: number;
  text: string;
  section: string;
}

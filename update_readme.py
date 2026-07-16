import re

# -----------------
# README.md
# -----------------
with open('e:/AI-based-project/urban-platform/README.md', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Remove the graph TD from 项目概况
text = re.sub(r'```mermaid\ngraph TD\n\s+UI\[Streamlit.*?```\n\n> 🎉 \*\*最新特性', '> 🎉 **最新特性', text, flags=re.DOTALL)

# 2. Insert Diagram 1 under 1. 🎨 GIS-to-AIGC 空间对齐与制图管线
diagram_1_zh = '''
```mermaid
flowchart LR
    A[(GIS 矢量数据)] -->|数据预处理脚本| B(矢量光栅化模块)
    
    subgraph 空间约束特征图
        B --> C1[Canny: 骨架特征]
        B --> C2[Seg: 语义分割]
        B --> C3[Tile: 环境底图]
    end
    
    C1 --> SD{视觉生成引擎}
    C2 --> SD
    C3 --> SD
    
    subgraph 智能化制图管线
        P[大语言模型提示词引擎] --> SD
        SD --> Q[多模态双重质量评估]
        Q -->|满足规范| Out[专业级规划图纸输出]
        Q -->|不满足规范| P
    end
```
'''
text = re.sub(r'(### 1\. 🎨 GIS-to-AIGC 空间对齐与制图管线[^\n]*\n.*?保证最终产出百分之百符合工程绘图规范。)', r'\1\n' + diagram_1_zh, text, flags=re.DOTALL)

# 3. Replace Diagram 2 under 2. 🤝 多主体决策博弈推演系统
diagram_2_zh = '''```mermaid
sequenceDiagram
    participant P as 角色 A (合规与全局利益)
    participant D as 角色 B (经济效益考量)
    participant R as 角色 C (品质与权益保障)
    participant RAG as 政策知识库引擎
    
    Note over P, R: 核心议题多轮博弈与谈判
    P->>RAG: 检索空间规划法规约束
    RAG-->>P: 返回空间限制条件
    P->>D: 提出合规性限制与初步方案
    D->>R: 基于经济效益提出补偿方案
    R->>P: 反馈诉求并提出调整建议
    Note over P, R: 大语言模型评估各方让步与共识
    P->>P: 动态更新共识度雷达
    P->>P: 输出利益平衡策略矩阵
```'''
text = re.sub(r'```mermaid\nsequenceDiagram\n\s+participant P as 规划师.*?```', diagram_2_zh, text, flags=re.DOTALL)

# 4. Insert Diagram 3 under 3. 📊 数据-逻辑分离与 MPI/GVI 循证诊断系统
diagram_3_zh = '''
```mermaid
graph TD
    subgraph 空间数据底座 (解耦设计)
        D1[三维建筑与形态数据]
        D2[街景与环境感知数据]
        D3[POI与功能业态数据]
        D4[多源舆情与社会数据]
    end
    
    subgraph 核心分析引擎
        E1[空间与形态计算模型]
        E2[环境视觉质量分析模型]
        E3[商业活力评估模型]
        E4[自然语言情感提取模型]
    end
    
    D1 -.-> E1
    D2 -.-> E2
    D3 -.-> E3
    D4 -.-> E4
    
    subgraph 决策输出层
        E1 --> AHP[多维指标融合计算权重]
        E2 --> AHP
        E3 --> AHP
        E4 --> AHP
        AHP --> Out1[目标区域更新潜力排名]
        AHP --> Out2[多维度现状诊断雷达图]
    end
```
'''
text = re.sub(r'(### 3\. 📊 数据-逻辑分离与 MPI/GVI 循证诊断系统.*?低成本的平台复用与业务拓展。)', r'\1\n' + diagram_3_zh, text, flags=re.DOTALL)

# 5. Remove the AIGC diagram from ## ⚙️ 技术架构
text = re.sub(r'### 🎨 AIGC 制图管线\n\n```mermaid\nflowchart LR\n.*?```\n\n### ⚡ 性能优化', '### ⚡ 性能优化', text, flags=re.DOTALL)

with open('e:/AI-based-project/urban-platform/README.md', 'w', encoding='utf-8') as f:
    f.write(text)


# -----------------
# README_EN.md
# -----------------
with open('e:/AI-based-project/urban-platform/README_EN.md', 'r', encoding='utf-8') as f:
    text_en = f.read()

# 1. Remove graph TD from Project Overview
text_en = re.sub(r'```mermaid\ngraph TD\n\s+UI\[Streamlit.*?```\n\n> 🎉 \*\*New Feature', '> 🎉 **New Feature', text_en, flags=re.DOTALL)

# 2. Remove Multi-Agent Negotiation Simulation from Strategy
text_en = re.sub(r'#### 🤖 Multi-Agent Negotiation Simulation \(Stage 07\)\n\n```mermaid\nsequenceDiagram.*?```\n\n### 🔴 Design', '### 🔴 Design', text_en, flags=re.DOTALL)

# 3. Remove AIGC Pipeline Architecture completely
text_en = re.sub(r'## ⚙️ AIGC Pipeline Architecture\n\n```mermaid\nflowchart LR\n.*?```\n\n---', '---', text_en, flags=re.DOTALL)

# 4. Insert Core Functional Modules section before Quick Start
core_modules_en = '''
## 🧩 Core Functional Modules

### 1. 🎨 Spatial Alignment & Mapping Pipeline
This platform eliminates spatial hallucination in generative AI for planning by utilizing a Vector→Raster→AIGC pipeline.
* **Spatial Constraint Extraction**: Converts GeoJSON vector layers into binary road skeletons, semantic landuse zoning, and building footprints.
* **End-to-End Orchestration**: The pipeline utilizes LLMs to generate professional prompts, injecting them alongside rasterized GIS images into the generative engine.
* **Dual Quality Loop**: A VLM assesses the visual quality while the LLM checks content compliance. Sub-standard drawings trigger automatic parameter adjustments and regeneration.

```mermaid
flowchart LR
    A[(GIS Vector Data)] -->|Data Preprocessing Script| B(Vector Rasterization Module)
    
    subgraph Spatial Constraint Features
        B --> C1[Canny: Skeleton Feature]
        B --> C2[Seg: Semantic Segmentation]
        B --> C3[Tile: Context Basemap]
    end
    
    C1 --> SD{Visual Generative Engine}
    C2 --> SD
    C3 --> SD
    
    subgraph Intelligent Mapping Pipeline
        P[LLM Prompt Engine] --> SD
        SD --> Q[Multimodal Dual Quality Assessment]
        Q -->|Meets Standard| Out[Professional Planning Drawing]
        Q -->|Below Standard| P
    end
```

### 2. 🤝 Multi-Agent Negotiation Simulation
The system upgrades static planning into a dynamic three-role game-theoretic simulation for urban renewal.
* **Closed-Loop Negotiation**: Agents simulate the interests of three major parties. They undergo rounds of Statements, Rebuttals, and Compromises on specific issues.
* **Policy Knowledge Constraints**: During negotiations, a RAG system retrieves regulations (e.g., heritage protection lines, height limits) to enforce compliance.
* **Consensus Quantification**: The system maps out the alignment of interests to generate a dynamic consensus radar and a final strategic matrix.

```mermaid
sequenceDiagram
    participant P as Agent A (Compliance & Public Interest)
    participant D as Agent B (Economic Viability)
    participant R as Agent C (Quality & Rights)
    participant RAG as Policy Knowledge Base
    
    Note over P, R: Multi-Round Issue Negotiation
    P->>RAG: Retrieve spatial planning regulations
    RAG-->>P: Return spatial constraints
    P->>D: Propose compliant initial plan
    D->>R: Offer compensation based on economics
    R->>P: Provide feedback & adjustment requests
    Note over P, R: LLM evaluates concessions & consensus
    P->>P: Dynamically update consensus radar
    P->>P: Output balanced strategy matrix
```

### 3. 📊 Evidence-Based Assessment System
Adhering to modern software engineering, the system achieves complete decoupling of spatial data from analytical logic.
* **Multi-Dimensional Fusion**: Synthesizes visual quality, spatial metrics, commercial vitality, and social sentiment into a comprehensive diagnosis.
* **Zero-Code Migration**: Expanding to a new urban plot requires no code changes—simply replacing the underlying geographic files automatically refreshes the entire digital twin base.

```mermaid
graph TD
    subgraph Spatial Data Base (Decoupled)
        D1[3D Morphology Data]
        D2[Street View & Context Data]
        D3[POI & Functional Data]
        D4[Social Sentiment Data]
    end
    
    subgraph Analytical Engines
        E1[Spatial Computation Model]
        E2[Visual Quality Assessment Model]
        E3[Commercial Vitality Model]
        E4[NLP Sentiment Extraction]
    end
    
    D1 -.-> E1
    D2 -.-> E2
    D3 -.-> E3
    D4 -.-> E4
    
    subgraph Decision Output Layer
        E1 --> AHP[Multi-Indicator Weight Fusion]
        E2 --> AHP
        E3 --> AHP
        E4 --> AHP
        AHP --> Out1[Target Area Renewal Potential Ranking]
        AHP --> Out2[Multi-Dimensional Diagnostic Radar]
    end
```
'''

text_en = re.sub(r'(## 🚀 Quick Start)', core_modules_en + r'\n\1', text_en, flags=re.DOTALL)

with open('e:/AI-based-project/urban-platform/README_EN.md', 'w', encoding='utf-8') as f:
    f.write(text_en)

print("Done")

# 零预置模板·纯数据驱动因地制宜城市更新平台 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建彻底剔除预置死模板的通用城市更新空间推演底盘，支持双轨制地块接入（文件上传与地图圈选）、空间数据算力动态推断痛点、利益相关方自生式博弈、气候与文脉自适应 AIGC 生形及全球自适应 UTM 投影工程 CAD 交付。

**Architecture:** 采用“数据接入双轨层 -> 因地制宜算法推断层 -> 三大工作台呈现层”的分离架构。所有角色人设、规划痛点、AIGC 提示词与 CAD 图纸均由算法根据地块真实定量数据现场推导，严禁任何固定模板。

**Tech Stack:** Python 3.14, Streamlit 1.55, GeoPandas, Shapely, PyProj (UTM), Plotly, DeepSeek LLM, AutoCAD DXF (AC1015, ANSI_936).

---

### Task 1: 因地制宜核心推断引擎 (`src/engines/context_adaptive_engine.py`)

**Files:**
- Create: `src/engines/context_adaptive_engine.py`
- Test: `tests/unit/test_context_adaptive_engine.py`

- [ ] **Step 1: 编写单元测试**

```python
def test_infer_plot_diagnostics_for_industrial():
    plot = {"name": "老铸造车间", "land_use": "工业用地", "area_ha": 3.5, "gvi_mean": 0.08, "poi_count": 5}
    issues = infer_plot_diagnostics(plot)
    assert any("闲置" in s or "工业" in s or "转型" in s for s in issues)
    assert any("绿化" in s or "绿视率" in s for s in issues)

def test_generate_adaptive_personas_derives_real_stakeholders():
    plot = {"name": "朝阳南里", "land_use": "居住用地", "issues": ["老龄化严重", "管网老化"]}
    site = {"city": "北京", "climate": "北方温带干冷"}
    personas = generate_adaptive_personas(site, plot)
    assert len(personas) == 3
    # 必须反映真实利益主体（老龄/居民代表、物业/社区运营、街道/规划监管）
    names = [p["role_title"] for p in personas]
    assert any("居民" in n or "业主" in n for n in names)
    assert any("运营" in n or "物业" in n for n in names)
    assert any("规划" in n or "监管" in n for n in names)
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/unit/test_context_adaptive_engine.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: 实现 `src/engines/context_adaptive_engine.py`**
  - `infer_plot_diagnostics(plot_data, site_context=None)`: 纯算法从面积、用地类型、GVI、POI、建筑密度推断真实空间痛点；
  - `generate_adaptive_personas(site_context, target_plot, regulatory_limits=None)`: 动态构建 3 组真实相关方 Prompt（原住/使用人群、投资/运营实体、规划/法定义务人）；
  - `generate_adaptive_aigc_prompt(site_context, target_plot, consensus)`: 基于经纬度计算气候特征（防寒向阳/遮阳通风/退台等），结合博弈共识关键词生成 AIGC Prompt；
  - `get_utm_epsg_for_coordinates(lon, lat)`: 自动计算全球通用的 UTM 投影带 EPSG 代号。

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/unit/test_context_adaptive_engine.py -v`
Expected: PASS

- [ ] **Step 5: 提交代码**

`git add src/engines/context_adaptive_engine.py tests/unit/test_context_adaptive_engine.py; git commit -m "feat: implement context adaptive inference engine"`

---

### Task 2: 双轨制地块接入面板 (`src/ui/site_ingestion_panel.py`)

**Files:**
- Create: `src/ui/site_ingestion_panel.py`
- Modify: `src/config/site.py`
- Test: `tests/unit/test_site_ingestion.py`

- [ ] **Step 1: 编写单元测试**

```python
def test_parse_uploaded_geojson_updates_runtime_site():
    sample_geojson = {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[[114.3, 30.5], [114.31, 30.5], [114.31, 30.51], [114.3, 30.5]]]}}]
    }
    site = parse_site_geometry_from_geojson(sample_geojson, city="武汉", name="汉阳铁厂")
    assert site["city"] == "武汉"
    assert site["center"][0] == pytest.approx(114.305, 0.01)
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/unit/test_site_ingestion.py -v`
Expected: FAIL

- [ ] **Step 3: 实现地块双轨接入逻辑**
  - 实现 `parse_site_geometry_from_geojson` 与 `parse_plots_from_geojson`；
  - 实现 `render_site_ingestion_modal()`:
    - 选项 A：上传 GeoJSON / Shapefile / DXF；
    - 选项 B：手动输入经纬度 / 城市名称，自动调用后台 `osm_fetcher` 拉取建筑路网底模；
    - 填写法定控规红线（限高、容积率、密度）；
  - 将激活数据更新到运行时会话状态中，确保下游无缝读取。

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/unit/test_site_ingestion.py -v`
Expected: PASS

- [ ] **Step 5: 提交代码**

`git add src/ui/site_ingestion_panel.py src/config/site.py tests/unit/test_site_ingestion.py; git commit -m "feat: add dual-track site ingestion panel"`

---

### Task 3: 工作台 1 重构 —— 任意地块自由量化诊断与靶向锁定

**Files:**
- Modify: `pages/01_全息空间诊断与数据沙盘.py`
- Modify: `src/stages/stage04_diagnosis/page.py`
- Test: `tests/unit/test_stage04_dynamic_plot_selection.py`

- [ ] **Step 1: 编写单元测试**

```python
def test_user_can_select_any_plot_as_target():
    # 验证无论传入何种地块（如"市一中北侧"或自定义地块），系统均能自动推导其痛点并存入总线
    select_target_plot_and_diagnose(plot_name="市一中北侧", land_use="科教文卫用地", mpi_score=78.2)
    saved = load_stage_output("04", "target_plot")
    assert saved["name"] == "市一中北侧"
    assert len(saved["issues"]) > 0
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/unit/test_stage04_dynamic_plot_selection.py -v`
Expected: FAIL

- [ ] **Step 3: 重构 Stage 04 诊断逻辑**
  - 在 MPI 评估与地块雷达中接入动态选择器：用户可从列表中勾选**任意地块**，或点击“设为当前更新靶向地块”；
  - 调用 `infer_plot_diagnostics` 动态生成该地块的真实痛点与特征；
  - 呈现“🎯 靶向地块动态诊断画像”，并将数据保存至 `save_stage_output("04", "target_plot", plot_data)`。

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/unit/test_stage04_dynamic_plot_selection.py -v`
Expected: PASS

- [ ] **Step 5: 提交代码**

`git add pages/01_全息空间诊断与数据沙盘.py src/stages/stage04_diagnosis/page.py tests/unit/test_stage04_dynamic_plot_selection.py; git commit -m "feat: enable universal plot diagnosis and free target selection in stage 04"`

---

### Task 4: 工作台 2 重构 —— 场景自生式多主体博弈与自适应 AIGC

**Files:**
- Modify: `pages/02_多主体博弈与空间AIGC工坊.py`
- Modify: `src/stages/stage07_strategy/page.py`
- Modify: `src/workflow/design_context.py`
- Modify: `src/stages/stage10_detail_design/page.py`
- Test: `tests/unit/test_adaptive_game_and_aigc.py`

- [ ] **Step 1: 编写单元测试**

```python
def test_stage07_generates_dynamic_roles_based_on_target_plot():
    # 模拟输入一个工业地块
    set_target_plot({"name": "化工厂老区", "land_use": "工业/仓储", "issues": ["重工业污染", "大跨度厂房闲置"]})
    personas = build_stage07_personas()
    assert any("工人" in p or "产业" in p for p in personas.keys())
    assert "水产大市场" not in str(personas)
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/unit/test_adaptive_game_and_aigc.py -v`
Expected: FAIL

- [ ] **Step 3: 重构 Stage 07 与 AIGC 生形逻辑**
  - 彻底移除硬编码角色（老王/赵总/李工关于长春水产市场的台词）；
  - 调用 `generate_adaptive_personas()` 现场生成角色与初始诉求；
  - 重构 `synthesize_design_brief()`，动态注入当前地块名、用地性质、博弈共识关键词；
  - 在 Stage 10 与 Stage 15 中调用 `generate_adaptive_aigc_prompt()` 生成风貌与刚性约束提示词。

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/unit/test_adaptive_game_and_aigc.py -v`
Expected: PASS

- [ ] **Step 5: 提交代码**

`git add pages/02_多主体博弈与空间AIGC工坊.py src/stages/stage07_strategy/page.py src/workflow/design_context.py src/stages/stage10_detail_design/page.py tests/unit/test_adaptive_game_and_aigc.py; git commit -m "feat: dynamic stakeholders game theory and adaptive aigc prompting"`

---

### Task 5: 工作台 3 重构 —— 全球 UTM 投影与法定导则动态装配

**Files:**
- Modify: `pages/03_数字图则与工程交付枢纽.py`
- Modify: `src/stages/stage12_guideline/page.py`
- Modify: `src/stages/stage13_outputs/page.py`
- Modify: `src/utils/vector_exporter.py`
- Test: `tests/unit/test_universal_cad_and_guidelines.py`

- [ ] **Step 1: 编写单元测试**

```python
def test_export_dxf_for_arbitrary_city_projection():
    # 传入南方广州坐标 (113.3, 23.1)
    gdf = create_mock_gdf_at(113.3, 23.1)
    dxf_path = export_universal_dxf(gdf, output_path="output/test_gz.dxf")
    assert os.path.exists(dxf_path)
    # 验证是否正确投影到了 UTM Zone 49N / 50N
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/unit/test_universal_cad_and_guidelines.py -v`
Expected: FAIL

- [ ] **Step 3: 落实通用交付逻辑**
  - Stage 12: 读取当前靶向地块的测绘数据与多主体博弈敲定的控规指标，生成图文并茂的法定导则；
  - Stage 13: 矢量 CAD 导出引擎根据真实经度自动切换 UTM 代号，生成标准 GB/T 国标图层 DXF。

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/unit/test_universal_cad_and_guidelines.py -v`
Expected: PASS

- [ ] **Step 5: 提交代码**

`git add pages/03_数字图则与工程交付枢纽.py src/stages/stage12_guideline/page.py src/stages/stage13_outputs/page.py src/utils/vector_exporter.py tests/unit/test_universal_cad_and_guidelines.py; git commit -m "feat: universal utm projection cad and dynamic statutory guidelines"`

---

### Task 6: 全链路回归测试与冒烟测试验证

**Files:**
- Test: `tests/` 全量套件
- Script: `tools/startup_smoke.py`, `tools/check_env.py`

- [ ] **Step 1: 运行全量单元与集成测试**

Run: `pytest`
Expected: 全部测试通过，无回归缺陷。

- [ ] **Step 2: 运行启动与环境冒烟测试**

Run: `python tools/startup_smoke.py`
Run: `python tools/check_env.py`
Expected: `[OK] SUCCESS`

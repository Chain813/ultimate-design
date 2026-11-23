import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import { MapboxOverlay } from "@deck.gl/mapbox";
import { AmbientLight, DirectionalLight, LightingEffect } from "@deck.gl/core";
import { ColumnLayer, GeoJsonLayer, ScatterplotLayer } from "@deck.gl/layers";
import { HeatmapLayer } from "@deck.gl/aggregation-layers";
import {
  Compass,
  Eye,
  Layers,
  Lock,
  Maximize2,
  RotateCcw,
  Sun,
} from "lucide-react";
import { fetchBinaryLayer, getMvtTileUrl } from "../services/apiClient";
import { useStudioStore } from "../store/useStudioStore";
import type {
  BinaryLayerPayload,
  FusedPlot,
  GeoJsonFeature,
  SolarSeasonKey,
  SyntaxMetricKey,
} from "../types/api";

export type LayerKey =
  | "boundary"
  | "plots"
  | "buildings"
  | "syntax"
  | "landuse"
  | "roads"
  | "rails"
  | "water"
  | "gvi"
  | "poi"
  | "traffic";

export interface SpatialMap3DProps {
  selectedPlotId?: string | null;
  onSelectPlot?: (plotId: string, plot?: FusedPlot) => void;
  onLockPlot?: (plot: FusedPlot) => void;
  height?: string | number;
  className?: string;
  initialCenter?: [number, number];
  initialZoom?: number;
  initialPitch?: number;
  defaultLayers?: Partial<Record<LayerKey, boolean>>;
  syntaxMetric?: SyntaxMetricKey;
  compactHud?: boolean;
}

const DEFAULT_CENTER: [number, number] = [125.3245, 43.8868]; // Changchun urban core

const LAYER_LABELS: Array<{ key: LayerKey; label: string; color: string }> = [
  { key: "boundary", label: "研究红线", color: "#ef4444" },
  { key: "plots", label: "重点地块", color: "#0071e3" },
  { key: "buildings", label: "3D建筑白模", color: "#64748b" },
  { key: "syntax", label: "空间句法路网", color: "#f59e0b" },
  { key: "landuse", label: "用地现状", color: "#10b981" },
  { key: "roads", label: "城市路网", color: "#94a3b8" },
  { key: "rails", label: "轨道交通", color: "#475569" },
  { key: "water", label: "水系格局", color: "#38bdf8" },
  { key: "gvi", label: "GVI绿视3D柱", color: "#22c55e" },
  { key: "poi", label: "POI活力热力", color: "#ec4899" },
  { key: "traffic", label: "交通负荷节点", color: "#8b5cf6" },
];

const SYNTAX_METRICS: Array<{ key: SyntaxMetricKey; label: string }> = [
  { key: "int_r400", label: "R400m 步行整合度" },
  { key: "int_r800", label: "R800m 街区整合度" },
  { key: "int_rn", label: "全局 Rn 整合度" },
  { key: "choice_norm", label: "Brandes 穿行度 Choice" },
];

const SEASON_DECLINATION: Record<SolarSeasonKey, { label: string; declDeg: number }> = {
  winter: { label: "冬至日照", declDeg: -23.44 },
  equinox: { label: "春/秋分", declDeg: 0.0 },
  summer: { label: "夏至日照", declDeg: 23.44 },
};

/**
 * Compute solar directional vector + ambient intensity for latitude ~43.88N
 */
function computeSolarLighting(hour: number, season: SolarSeasonKey) {
  const latRad = (43.8868 * Math.PI) / 180;
  const declRad = (SEASON_DECLINATION[season].declDeg * Math.PI) / 180;
  const hourAngleRad = ((hour - 12) * 15 * Math.PI) / 180;

  const sinAlt =
    Math.sin(latRad) * Math.sin(declRad) +
    Math.cos(latRad) * Math.cos(declRad) * Math.cos(hourAngleRad);
  const altitude = Math.asin(Math.max(-0.8, Math.min(0.98, sinAlt)));

  const cosAz =
    (Math.sin(declRad) - Math.sin(latRad) * Math.sin(altitude)) /
    Math.max(0.001, Math.cos(latRad) * Math.cos(altitude));
  let azimuth = Math.acos(Math.max(-1, Math.min(1, cosAz)));
  if (hour > 12) {
    azimuth = 2 * Math.PI - azimuth;
  }

  const isDaytime = altitude > 0.03;
  const dirX = -Math.cos(altitude) * Math.sin(azimuth);
  const dirY = -Math.cos(altitude) * Math.cos(azimuth);
  const dirZ = -Math.max(0.2, Math.sin(altitude));

  // Warm golden hour tint vs crisp daylight vs moonlight
  const sunColor: [number, number, number] = !isDaytime
    ? [120, 145, 195]
    : altitude < 0.28
    ? [255, 204, 145]
    : [255, 250, 242];

  const ambientIntensity = isDaytime
    ? 0.55 + 0.35 * Math.sin(altitude)
    : 0.35;
  const directionalIntensity = isDaytime
    ? 1.15 + 0.85 * Math.sin(altitude)
    : 0.45;

  return {
    direction: [dirX, dirY, dirZ] as [number, number, number],
    sunColor,
    ambientIntensity,
    directionalIntensity,
    altitudeDeg: Math.round((altitude * 180) / Math.PI),
    azimuthDeg: Math.round((azimuth * 180) / Math.PI),
    isDaytime,
  };
}

/**
 * Self-contained Apple HIG Light offline vector canvas style so MapLibre never white-screens offline
 */
function buildOfflineAppleHigStyle(): maplibregl.StyleSpecification {
  return {
    version: 8,
    name: "UltimateDESIGN-AppleHIG-Offline",
    sources: {},
    layers: [
      {
        id: "ud-offline-bg",
        type: "background",
        paint: {
          "background-color": "#eef2f6",
        },
      },
    ],
  };
}

/**
 * Compute centroid [lon, lat] of a GeoJSON Polygon/MultiPolygon feature
 */
function getFeatureCentroid(feat?: GeoJsonFeature | null): [number, number] | null {
  if (!feat || !feat.geometry || !feat.geometry.coordinates) return null;
  const { type, coordinates } = feat.geometry;
  let ring: number[][] = [];
  if (type === "Polygon" && Array.isArray(coordinates[0])) {
    ring = coordinates[0];
  } else if (
    type === "MultiPolygon" &&
    Array.isArray(coordinates[0]) &&
    Array.isArray(coordinates[0][0])
  ) {
    ring = coordinates[0][0];
  } else if (type === "Point" && Array.isArray(coordinates)) {
    return [Number(coordinates[0]), Number(coordinates[1])];
  }
  if (!ring.length) return null;
  let sumLon = 0;
  let sumLat = 0;
  let count = 0;
  for (const pt of ring) {
    if (Array.isArray(pt) && pt.length >= 2) {
      sumLon += Number(pt[0]);
      sumLat += Number(pt[1]);
      count += 1;
    }
  }
  return count > 0 ? [sumLon / count, sumLat / count] : null;
}

/**
 * Build DepthMapX Blue -> Cyan -> Green -> Yellow -> Red color expression for MapLibre
 */
function buildDepthMapXColorExpression(metric: SyntaxMetricKey): any {
  const maxVal =
    metric === "choice_norm"
      ? 0.45
      : metric === "int_r400"
      ? 2.4
      : metric === "int_r800"
      ? 2.2
      : 1.8;

  const valExpr = ["coalesce", ["to-number", ["get", metric]], 0];
  return [
    "interpolate",
    ["linear"],
    valExpr,
    0,
    "#2563eb", // Low Integration / Choice (Cold Blue)
    maxVal * 0.25,
    "#06b6d4", // Cyan
    maxVal * 0.5,
    "#22c55e", // Green
    maxVal * 0.75,
    "#eab308", // Yellow
    maxVal,
    "#ef4444", // High Core Integration / Choice (Hot Red)
  ];
}

export const SpatialMap3D: React.FC<SpatialMap3DProps> = ({
  selectedPlotId: propSelectedPlotId,
  onSelectPlot,
  onLockPlot,
  height = "100%",
  className = "",
  initialCenter = DEFAULT_CENTER,
  initialZoom = 13.7,
  initialPitch = 52,
  defaultLayers,
  syntaxMetric: propSyntaxMetric,
  compactHud = false,
}) => {
  const {
    activeProjectId,
    fusedPlots,
    fusedPlotsGeojson,
    boundaryGeojson,
    selectedPlotId: storeSelectedPlotId,
    lockedTargetPlot,
    setSelectedPlotId,
    lockTargetPlot,
  } = useStudioStore();

  const effectiveSelectedPlotId =
    propSelectedPlotId !== undefined ? propSelectedPlotId : storeSelectedPlotId;

  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const deckOverlayRef = useRef<MapboxOverlay | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [offlineFallbackActive, setOfflineFallbackActive] = useState(false);
  const [liveFps, setLiveFps] = useState<number>(
    () => window.udDesktop?.runtimeConfig?.displayRefreshHz || 60
  );
  const unlockFpsActive = Boolean(window.udDesktop?.runtimeConfig?.unlockFps);

  // Measure real native refresh cadence (60 / 120 / 144 / 240+ FPS)
  useEffect(() => {
    let rafId = 0;
    let frames = 0;
    let lastTs = performance.now();
    const tick = (now: number) => {
      frames += 1;
      const elapsed = now - lastTs;
      if (elapsed >= 600) {
        setLiveFps(Math.round((frames * 1000) / elapsed));
        frames = 0;
        lastTs = now;
      }
      rafId = requestAnimationFrame(tick);
    };
    rafId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafId);
  }, []);

  // Layer toggles
  const [visibleLayers, setVisibleLayers] = useState<Record<LayerKey, boolean>>({
    boundary: true,
    plots: true,
    buildings: true,
    syntax: true,
    landuse: true,
    roads: true,
    rails: true,
    water: true,
    gvi: false,
    poi: false,
    traffic: false,
    ...(defaultLayers || {}),
  });

  // Solar & Space Syntax controls
  const [solarHour, setSolarHour] = useState<number>(14.5);
  const [solarSeason, setSolarSeason] = useState<SolarSeasonKey>("equinox");
  const [is3DPitch, setIs3DPitch] = useState<boolean>(initialPitch > 10);
  const [syntaxMetric, setSyntaxMetric] = useState<SyntaxMetricKey>(
    propSyntaxMetric || "int_r800"
  );
  const [layerDrawerOpen, setLayerDrawerOpen] = useState<boolean>(!compactHud);

  // Hover tooltip state
  const [hoverPlot, setHoverPlot] = useState<{
    x: number;
    y: number;
    plot: FusedPlot;
  } | null>(null);

  // Binary typed-array layers cache
  const [binaryCache, setBinaryCache] = useState<
    Partial<Record<"gvi" | "poi" | "traffic", BinaryLayerPayload>>
  >({});

  useEffect(() => {
    if (propSyntaxMetric) {
      setSyntaxMetric(propSyntaxMetric);
    }
  }, [propSyntaxMetric]);

  // Mount local MVT vector tile sources & layers onto MapLibre instance
  const attachLocalMvtLayers = useCallback(
    (map: maplibregl.Map) => {
      const mvtConfigs: Array<{
        sourceId: string;
        layerName: string;
        layerSpec: maplibregl.LayerSpecification;
        visibilityKey: LayerKey;
      }> = [
        {
          sourceId: "ud-mvt-water",
          layerName: "water",
          visibilityKey: "water",
          layerSpec: {
            id: "ud-layer-water",
            type: "fill",
            source: "ud-mvt-water",
            "source-layer": "water",
            paint: {
              "fill-color": "#a5d8ff",
              "fill-opacity": 0.75,
            },
          },
        },
        {
          sourceId: "ud-mvt-landuse",
          layerName: "landuse",
          visibilityKey: "landuse",
          layerSpec: {
            id: "ud-layer-landuse",
            type: "fill",
            source: "ud-mvt-landuse",
            "source-layer": "landuse",
            paint: {
              "fill-color": [
                "coalesce",
                ["get", "color"],
                ["get", "Color"],
                "#bbf7d0",
              ] as any,
              "fill-opacity": 0.42,
            },
          },
        },
        {
          sourceId: "ud-mvt-roads",
          layerName: "roads",
          visibilityKey: "roads",
          layerSpec: {
            id: "ud-layer-roads",
            type: "line",
            source: "ud-mvt-roads",
            "source-layer": "roads",
            paint: {
              "line-color": "#94a3b8",
              "line-width": [
                "interpolate",
                ["linear"],
                ["zoom"],
                11,
                0.8,
                15,
                2.4,
              ] as any,
              "line-opacity": 0.75,
            },
          },
        },
        {
          sourceId: "ud-mvt-rails",
          layerName: "rails",
          visibilityKey: "rails",
          layerSpec: {
            id: "ud-layer-rails",
            type: "line",
            source: "ud-mvt-rails",
            "source-layer": "rails",
            paint: {
              "line-color": "#475569",
              "line-width": 2.0,
              "line-dasharray": [3, 2],
            },
          },
        },
        {
          sourceId: "ud-mvt-syntax",
          layerName: "road_syntax_v2",
          visibilityKey: "syntax",
          layerSpec: {
            id: "ud-layer-syntax",
            type: "line",
            source: "ud-mvt-syntax",
            "source-layer": "road_syntax_v2",
            paint: {
              "line-color": buildDepthMapXColorExpression(syntaxMetric),
              "line-width": [
                "interpolate",
                ["linear"],
                ["zoom"],
                11,
                1.6,
                15,
                4.2,
              ] as any,
              "line-opacity": 0.92,
            },
          },
        },
        {
          sourceId: "ud-mvt-buildings",
          layerName: "buildings",
          visibilityKey: "buildings",
          layerSpec: {
            id: "ud-layer-buildings",
            type: "fill-extrusion",
            source: "ud-mvt-buildings",
            "source-layer": "buildings",
            paint: {
              "fill-extrusion-color": [
                "case",
                [
                  "any",
                  ["==", ["get", "is_historical"], true],
                  ["==", ["get", "is_historical"], 1],
                  ["==", ["get", "is_historical"], "1"],
                ],
                "#d97706",
                [
                  "interpolate",
                  ["linear"],
                  [
                    "coalesce",
                    ["to-number", ["get", "height_m"]],
                    ["*", ["to-number", ["get", "floor"]], 3.2],
                    12,
                  ],
                  0,
                  "#e2e8f0",
                  24,
                  "#cbd5e1",
                  60,
                  "#93c5fd",
                  110,
                  "#3b82f6",
                ],
              ] as any,
              "fill-extrusion-height": [
                "coalesce",
                ["to-number", ["get", "height_m"]],
                ["*", ["to-number", ["get", "floor"]], 3.2],
                12,
              ] as any,
              "fill-extrusion-base": 0,
              "fill-extrusion-opacity": 0.86,
            },
          },
        },
      ];

      for (const cfg of mvtConfigs) {
        if (!map.getSource(cfg.sourceId)) {
          map.addSource(cfg.sourceId, {
            type: "vector",
            tiles: [getMvtTileUrl(cfg.layerName)],
            minzoom: 9,
            maxzoom: 18,
          });
        }
        if (!map.getLayer(cfg.layerSpec.id)) {
          map.addLayer({
            ...cfg.layerSpec,
            layout: {
              visibility: visibleLayers[cfg.visibilityKey] ? "visible" : "none",
            },
          } as any);
        }
      }
    },
    [syntaxMetric, visibleLayers]
  );

  // Initialize MapLibre GL + Deck.GL MapboxOverlay
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const isOfflineEnv =
      typeof navigator !== "undefined" && navigator.onLine === false;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: isOfflineEnv
        ? buildOfflineAppleHigStyle()
        : "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
      center: initialCenter,
      zoom: initialZoom,
      pitch: initialPitch,
      bearing: -14,
      attributionControl: false,
    });

    if (isOfflineEnv) {
      setOfflineFallbackActive(true);
    }

    const deckOverlay = new MapboxOverlay({
      interleaved: true,
      layers: [],
    });

    map.addControl(deckOverlay as any);
    map.addControl(
      new maplibregl.NavigationControl({ visualizePitch: true }),
      "bottom-right"
    );

    let fallbackTriggered = isOfflineEnv;
    map.on("error", (ev: any) => {
      const msg = String(ev?.error?.message || "");
      if (
        !fallbackTriggered &&
        (msg.includes("cartocdn") ||
          msg.includes("Failed to fetch") ||
          msg.includes("ERR_"))
      ) {
        fallbackTriggered = true;
        setOfflineFallbackActive(true);
        map.setStyle(buildOfflineAppleHigStyle());
        map.once("styledata", () => {
          attachLocalMvtLayers(map);
          setMapLoaded(true);
        });
      }
    });

    map.on("load", () => {
      attachLocalMvtLayers(map);
      setMapLoaded(true);
    });

    mapRef.current = map;
    deckOverlayRef.current = deckOverlay;

    return () => {
      map.remove();
      mapRef.current = null;
      deckOverlayRef.current = null;
    };
  }, []);

  // Re-attach MVT sources when activeProjectId changes
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded) return;
    const layerIds = [
      "ud-layer-water",
      "ud-layer-landuse",
      "ud-layer-roads",
      "ud-layer-rails",
      "ud-layer-syntax",
      "ud-layer-buildings",
    ];
    const sourceIds = [
      "ud-mvt-water",
      "ud-mvt-landuse",
      "ud-mvt-roads",
      "ud-mvt-rails",
      "ud-mvt-syntax",
      "ud-mvt-buildings",
    ];
    layerIds.forEach((lid) => {
      if (map.getLayer(lid)) map.removeLayer(lid);
    });
    sourceIds.forEach((sid) => {
      if (map.getSource(sid)) map.removeSource(sid);
    });
    attachLocalMvtLayers(map);
  }, [activeProjectId, mapLoaded, attachLocalMvtLayers]);

  // Sync MVT layer visibility & Space Syntax metric color ramp
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded) return;

    const pairs: Array<[string, LayerKey]> = [
      ["ud-layer-water", "water"],
      ["ud-layer-landuse", "landuse"],
      ["ud-layer-roads", "roads"],
      ["ud-layer-rails", "rails"],
      ["ud-layer-syntax", "syntax"],
      ["ud-layer-buildings", "buildings"],
    ];

    for (const [layerId, key] of pairs) {
      if (map.getLayer(layerId)) {
        map.setLayoutProperty(
          layerId,
          "visibility",
          visibleLayers[key] ? "visible" : "none"
        );
      }
    }

    if (map.getLayer("ud-layer-syntax")) {
      map.setPaintProperty(
        "ud-layer-syntax",
        "line-color",
        buildDepthMapXColorExpression(syntaxMetric)
      );
    }
  }, [visibleLayers, syntaxMetric, mapLoaded]);

  // Lazy load zero-copy binary TypedArray layers (gvi, poi, traffic) when toggled on
  useEffect(() => {
    const binaryKeys: Array<"gvi" | "poi" | "traffic"> = ["gvi", "poi", "traffic"];
    binaryKeys.forEach((bKey) => {
      if (visibleLayers[bKey] && !binaryCache[bKey]) {
        fetchBinaryLayer(bKey)
          .then((payload) => {
            setBinaryCache((prev) => ({ ...prev, [bKey]: payload }));
          })
          .catch(() => {
            // Keep empty if endpoint has no binary points yet
          });
      }
    });
  }, [visibleLayers, binaryCache, activeProjectId]);

  // Smooth camera flyTo when selectedPlotId changes from the right-hand table/radar
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !effectiveSelectedPlotId) return;

    let targetCoord: [number, number] | null = null;
    const plotMeta = fusedPlots.find(
      (p) => String(p.plot_id) === String(effectiveSelectedPlotId)
    );
    if (plotMeta?.lon && plotMeta?.lat) {
      targetCoord = [Number(plotMeta.lon), Number(plotMeta.lat)];
    } else if (plotMeta?.centroid && plotMeta.centroid.length === 2) {
      targetCoord = [Number(plotMeta.centroid[0]), Number(plotMeta.centroid[1])];
    } else if (fusedPlotsGeojson?.features) {
      const feat = fusedPlotsGeojson.features.find(
        (f) =>
          String(f.properties?.plot_id || f.properties?.id || f.id) ===
          String(effectiveSelectedPlotId)
      );
      targetCoord = getFeatureCentroid(feat);
    }

    if (targetCoord && Number.isFinite(targetCoord[0]) && Number.isFinite(targetCoord[1])) {
      map.flyTo({
        center: targetCoord,
        zoom: Math.max(map.getZoom(), 14.8),
        duration: 900,
        essential: true,
      });
    }
  }, [effectiveSelectedPlotId, fusedPlots, fusedPlotsGeojson]);

  // Lookup plot metrics by plot_id
  const plotByIdMap = useMemo(() => {
    const m = new Map<string, FusedPlot>();
    fusedPlots.forEach((p) => {
      if (p.plot_id) m.set(String(p.plot_id), p);
    });
    return m;
  }, [fusedPlots]);

  // Convert binary Float32Array payload into structured point array for Deck.GL
  const buildBinaryPoints = useCallback((payload?: BinaryLayerPayload) => {
    if (!payload || !payload.data || payload.header.count <= 0) return [];
    const { count, stride, fields } = payload.header;
    const lonIdx = Math.max(0, fields.indexOf("lon"));
    const latIdx = Math.max(1, fields.indexOf("lat"));
    const valIdx = fields.length > 2 ? 2 : 0;
    const pts: Array<{ position: [number, number]; value: number; aux: number }> = [];
    const arr = payload.data;
    const maxItems = Math.min(count, Math.floor(arr.length / Math.max(1, stride)));
    for (let i = 0; i < maxItems; i++) {
      const base = i * stride;
      const lon = arr[base + lonIdx];
      const lat = arr[base + latIdx];
      if (!Number.isFinite(lon) || !Number.isFinite(lat)) continue;
      pts.push({
        position: [lon, lat],
        value: arr[base + valIdx] ?? 0.5,
        aux: stride > 3 ? arr[base + 3] : 0.5,
      });
    }
    return pts;
  }, []);

  const solarState = useMemo(
    () => computeSolarLighting(solarHour, solarSeason),
    [solarHour, solarSeason]
  );

  // Build Deck.GL interleaved layers + GPU LightingEffect
  useEffect(() => {
    const overlay = deckOverlayRef.current;
    if (!overlay) return;

    const layers: any[] = [];

    // 1. Study Scope Red Boundary Layer
    if (visibleLayers.boundary && boundaryGeojson?.features?.length) {
      layers.push(
        new GeoJsonLayer({
          id: "ud-deck-boundary",
          data: boundaryGeojson as any,
          filled: false,
          stroked: true,
          lineWidthMinPixels: 2.5,
          getLineColor: [239, 68, 68, 230],
          pickable: false,
        })
      );
    }

    // 2. Interactive Target Plots Layer (Bidirectional sync with diagnostic radar & table)
    if (visibleLayers.plots && fusedPlotsGeojson?.features?.length) {
      layers.push(
        new GeoJsonLayer({
          id: "ud-deck-fused-plots",
          data: fusedPlotsGeojson as any,
          pickable: true,
          stroked: true,
          filled: true,
          extruded: true,
          wireframe: true,
          lineWidthMinPixels: 2,
          getElevation: (f: any) => {
            const pid = String(
              f?.properties?.plot_id || f?.properties?.id || f?.id || ""
            );
            const isSelected = pid === String(effectiveSelectedPlotId || "");
            const isLocked = pid === String(lockedTargetPlot?.plot_id || "");
            return isLocked ? 22 : isSelected ? 16 : 6;
          },
          getFillColor: (f: any) => {
            const pid = String(
              f?.properties?.plot_id || f?.properties?.id || f?.id || ""
            );
            const isLocked = pid === String(lockedTargetPlot?.plot_id || "");
            const isSelected = pid === String(effectiveSelectedPlotId || "");
            if (isLocked) return [16, 185, 129, 175]; // Emerald locked target plot
            if (isSelected) return [0, 113, 227, 165]; // Apple HIG Accent Blue selected plot
            return [0, 113, 227, 72];
          },
          getLineColor: (f: any) => {
            const pid = String(
              f?.properties?.plot_id || f?.properties?.id || f?.id || ""
            );
            const isLocked = pid === String(lockedTargetPlot?.plot_id || "");
            const isSelected = pid === String(effectiveSelectedPlotId || "");
            if (isLocked) return [5, 150, 105, 255];
            if (isSelected) return [0, 113, 227, 255];
            return [30, 64, 175, 180];
          },
          updateTriggers: {
            getFillColor: [effectiveSelectedPlotId, lockedTargetPlot?.plot_id],
            getLineColor: [effectiveSelectedPlotId, lockedTargetPlot?.plot_id],
            getElevation: [effectiveSelectedPlotId, lockedTargetPlot?.plot_id],
          },
          onHover: (info: any) => {
            if (!info?.object) {
              setHoverPlot(null);
              return;
            }
            const props = info.object.properties || {};
            const pid = String(props.plot_id || props.id || info.object.id || "");
            const mergedPlot: FusedPlot = {
              plot_id: pid,
              name: props.name || pid,
              area_m2: Number(props.area_m2 || props.shape_area || 0),
              bldg_count: Number(props.bldg_count || 0),
              bcr: Number(props.bcr || 0),
              far: Number(props.far || 0),
              avg_floor: Number(props.avg_floor || 0),
              poi_density: Number(props.poi_density || 0),
              gvi_mean: Number(props.gvi_mean || 0),
              svf_mean: Number(props.svf_mean || 0),
              syntax_int_mean: Number(props.syntax_int_mean || 0),
              mpi_score: Number(props.mpi_score || 0),
              ...(plotByIdMap.get(pid) || {}),
            };
            setHoverPlot({
              x: info.x,
              y: info.y,
              plot: mergedPlot,
            });
          },
          onClick: (info: any) => {
            if (!info?.object) return;
            const props = info.object.properties || {};
            const pid = String(props.plot_id || props.id || info.object.id || "");
            if (!pid) return;
            const plotObj = plotByIdMap.get(pid) || (props as FusedPlot);
            setSelectedPlotId(pid);
            onSelectPlot?.(pid, plotObj);
          },
        })
      );
    }

    // 3. Zero-Copy Binary GVI / SVF 3D Cylinders
    if (visibleLayers.gvi && binaryCache.gvi) {
      const gviPts = buildBinaryPoints(binaryCache.gvi);
      if (gviPts.length > 0) {
        layers.push(
          new ColumnLayer({
            id: "ud-deck-gvi-columns",
            data: gviPts,
            diskResolution: 12,
            radius: 18,
            extruded: true,
            pickable: false,
            elevationScale: 180,
            getPosition: (d: any) => d.position,
            getElevation: (d: any) => Math.max(0.08, Number(d.value || 0.25)),
            getFillColor: (d: any) =>
              d.value >= 0.25 ? [16, 185, 129, 210] : [245, 158, 11, 210],
          })
        );
      }
    }

    // 4. Zero-Copy Binary POI Vitality Heatmap
    if (visibleLayers.poi && binaryCache.poi) {
      const poiPts = buildBinaryPoints(binaryCache.poi);
      if (poiPts.length > 0) {
        layers.push(
          new HeatmapLayer({
            id: "ud-deck-poi-heatmap",
            data: poiPts,
            getPosition: (d: any) => d.position,
            getWeight: (d: any) => Math.max(1, Number(d.value || 1)),
            radiusPixels: 38,
            intensity: 1.3,
            threshold: 0.05,
          })
        );
      }
    }

    // 5. Zero-Copy Binary Traffic Load Nodes
    if (visibleLayers.traffic && binaryCache.traffic) {
      const trafficPts = buildBinaryPoints(binaryCache.traffic);
      if (trafficPts.length > 0) {
        layers.push(
          new ScatterplotLayer({
            id: "ud-deck-traffic-nodes",
            data: trafficPts,
            getPosition: (d: any) => d.position,
            getRadius: (d: any) => Math.max(25, Number(d.value || 1) * 35),
            getFillColor: (d: any) =>
              d.value > 0.7 ? [239, 68, 68, 210] : [139, 92, 246, 195],
            pickable: false,
          })
        );
      }
    }

    // GPU Real-Time Solar LightingEffect
    const ambientLight = new AmbientLight({
      color: [255, 255, 255],
      intensity: solarState.ambientIntensity,
    });
    const sunDirectionalLight = new DirectionalLight({
      color: solarState.sunColor,
      intensity: solarState.directionalIntensity,
      direction: solarState.direction,
      _shadow: true,
    });
    const lightingEffect = new LightingEffect({
      ambientLight,
      sunDirectionalLight,
    });

    overlay.setProps({
      layers,
      effects: [lightingEffect],
    });
  }, [
    visibleLayers,
    boundaryGeojson,
    fusedPlotsGeojson,
    effectiveSelectedPlotId,
    lockedTargetPlot,
    binaryCache,
    solarState,
    plotByIdMap,
    buildBinaryPoints,
    setSelectedPlotId,
    onSelectPlot,
  ]);

  const toggleLayer = (key: LayerKey) => {
    setVisibleLayers((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleTogglePitch = () => {
    const map = mapRef.current;
    const next3D = !is3DPitch;
    setIs3DPitch(next3D);
    if (map) {
      map.easeTo({
        pitch: next3D ? 54 : 0,
        bearing: next3D ? -16 : 0,
        duration: 600,
      });
    }
  };

  const handleResetCamera = () => {
    const map = mapRef.current;
    if (!map) return;
    map.flyTo({
      center: initialCenter,
      zoom: initialZoom,
      pitch: is3DPitch ? 52 : 0,
      bearing: -14,
      duration: 850,
    });
  };

  const formatSolarTime = (val: number) => {
    const hrs = Math.floor(val);
    const mins = Math.round((val - hrs) * 60);
    return `${String(hrs).padStart(2, "0")}:${String(mins).padStart(2, "0")}`;
  };

  const currentlySelectedPlot = useMemo(() => {
    if (!effectiveSelectedPlotId) return null;
    return (
      plotByIdMap.get(String(effectiveSelectedPlotId)) ||
      lockedTargetPlot ||
      null
    );
  }, [effectiveSelectedPlotId, plotByIdMap, lockedTargetPlot]);

  return (
    <div
      className={`relative w-full overflow-hidden rounded-2xl border border-black/10 bg-[#eef2f6] select-none ${className}`}
      style={{ height }}
    >
      {/* MapLibre GL + Deck.GL Interleaved WebGL2 Canvas */}
      <div ref={containerRef} className="w-full h-full" />

      {/* Top-Left Floating GPU Sunlight, Space Syntax & Layer Control HUD */}
      <div className="absolute top-3 left-3 z-20 flex flex-col gap-2 max-w-[440px]">
        {/* Primary Bar: Solar Time Slider + Season + 2D/3D Pitch + Reset */}
        <div className="ud-glass-panel rounded-2xl px-3 py-2 flex flex-wrap items-center gap-2.5">
          <div className="flex items-center gap-1.5 text-[11.5px] font-bold text-[#1d1d1f]">
            <Sun
              className={`w-4 h-4 ${
                solarState.isDaytime ? "text-[#f59e0b]" : "text-[#6366f1]"
              }`}
            />
            <span>{formatSolarTime(solarHour)}</span>
          </div>

          <input
            type="range"
            min={6}
            max={20}
            step={0.25}
            value={solarHour}
            onChange={(e) => setSolarHour( parseFloat(e.target.value) )}
            className="w-24 accent-[#0071e3] cursor-pointer"
            title={`GPU 实时太阳高度角 ${solarState.altitudeDeg}° / 方位角 ${solarState.azimuthDeg}°`}
          />

          <select
            value={solarSeason}
            onChange={(e) => setSolarSeason(e.target.value as SolarSeasonKey)}
            className="px-2 py-1 rounded-lg bg-white/90 border border-black/10 text-[11px] font-semibold text-[#1d1d1f]"
          >
            <option value="winter">冬至日照</option>
            <option value="equinox">春秋分</option>
            <option value="summer">夏至日照</option>
          </select>

          <button
            type="button"
            onClick={handleTogglePitch}
            className={`px-2 py-1 rounded-lg text-[11px] font-bold border transition-colors ${
              is3DPitch
                ? "bg-[#0071e3] text-white border-[#0071e3]"
                : "bg-white text-[#1d1d1f] border-black/10"
            }`}
          >
            {is3DPitch ? "3D 轴测" : "2D 平面"}
          </button>

          <button
            type="button"
            onClick={handleResetCamera}
            className="p-1.5 rounded-lg bg-white hover:bg-black/5 border border-black/10 text-[#515154]"
            title="复位全域视角"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>

          <button
            type="button"
            onClick={() => setLayerDrawerOpen((v) => !v)}
            className={`flex items-center gap-1 px-2 py-1 rounded-lg text-[11px] font-semibold border ${
              layerDrawerOpen
                ? "bg-[#1d1d1f] text-white border-[#1d1d1f]"
                : "bg-white text-[#1d1d1f] border-black/10"
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>图层</span>
          </button>
        </div>

        {/* Collapsible 11-Layer Pills + Space Syntax Metric Selector */}
        {layerDrawerOpen && (
          <div className="ud-glass-panel rounded-2xl p-3 space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-[#1d1d1f]">
                DuckDB 动态 MVT 瓦片与零拷贝图层 (11 图层)
              </span>
              {offlineFallbackActive && (
                <span className="px-2 py-0.5 rounded-full bg-[#10b981]/15 text-[#065f46] text-[10px] font-semibold">
                  本地离线矢量底图已启用
                </span>
              )}
            </div>

            <div className="flex flex-wrap gap-1.5">
              {LAYER_LABELS.map((ly) => {
                const active = visibleLayers[ly.key];
                return (
                  <button
                    key={ly.key}
                    type="button"
                    onClick={() => toggleLayer(ly.key)}
                    className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold transition-all ${
                      active
                        ? "bg-white text-[#1d1d1f] shadow-2xs border border-black/15"
                        : "bg-black/5 text-[#6e6e73] border border-transparent opacity-70 hover:opacity-100"
                    }`}
                  >
                    <span
                      className="w-2 h-2 rounded-full"
                      style={{
                        backgroundColor: active ? ly.color : "#9ca3af",
                      }}
                    />
                    <span>{ly.label}</span>
                  </button>
                );
              })}
            </div>

            {visibleLayers.syntax && (
              <div className="pt-2 border-t border-black/8 flex items-center justify-between gap-2">
                <span className="text-[11px] font-semibold text-[#515154]">
                  rustworkx 空间句法指标:
                </span>
                <div className="flex items-center gap-1">
                  {SYNTAX_METRICS.map((sm) => (
                    <button
                      key={sm.key}
                      type="button"
                      onClick={() => setSyntaxMetric(sm.key)}
                      className={`px-2 py-0.5 rounded-md text-[10.5px] font-semibold transition-colors ${
                        syntaxMetric === sm.key
                          ? "bg-[#0071e3] text-white"
                          : "bg-white/80 hover:bg-white text-[#1d1d1f] border border-black/8"
                      }`}
                    >
                      {sm.label}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Top-Right Selected / Locked Target Plot Quick Action Card */}
      {currentlySelectedPlot && (
        <div className="ud-glass-panel absolute top-3 right-3 z-20 rounded-2xl p-3 w-[270px] space-y-2">
          <div className="flex items-center justify-between gap-2">
            <div className="min-w-0">
              <div className="text-[10px] font-bold text-[#0071e3] uppercase">
                当前选中更新单元
              </div>
              <div className="text-[13px] font-bold text-[#1d1d1f] truncate">
                {currentlySelectedPlot.name}
              </div>
            </div>
            <button
              type="button"
              onClick={() => {
                lockTargetPlot(currentlySelectedPlot);
                onLockPlot?.(currentlySelectedPlot);
              }}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-colors ${
                lockedTargetPlot?.plot_id === currentlySelectedPlot.plot_id
                  ? "bg-[#10b981] text-white"
                  : "bg-[#0071e3] hover:bg-[#0077ed] text-white"
              }`}
            >
              <Lock className="w-3 h-3" />
              <span>
                {lockedTargetPlot?.plot_id === currentlySelectedPlot.plot_id
                  ? "已锁定靶向"
                  : "锁定靶向"}
              </span>
            </button>
          </div>

          <div className="grid grid-cols-3 gap-1.5 text-[11px]">
            <div className="p-1.5 rounded-lg bg-white/80 border border-black/6">
              <div className="text-[10px] text-[#515154]">容积率 FAR</div>
              <div className="font-bold text-[#1d1d1f]">
                {Number(currentlySelectedPlot.far || 0).toFixed(2)}
              </div>
            </div>
            <div className="p-1.5 rounded-lg bg-white/80 border border-black/6">
              <div className="text-[10px] text-[#515154]">建筑密度</div>
              <div className="font-bold text-[#1d1d1f]">
                {(Number(currentlySelectedPlot.bcr || 0) * 100).toFixed(1)}%
              </div>
            </div>
            <div className="p-1.5 rounded-lg bg-white/80 border border-black/6">
              <div className="text-[10px] text-[#515154]">绿视率 GVI</div>
              <div className="font-bold text-[#10b981]">
                {(Number(currentlySelectedPlot.gvi_mean || 0) * 100).toFixed(1)}%
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Hover Tooltip for 3D Target Plot */}
      {hoverPlot && (
        <div
          className="ud-glass-panel pointer-events-none absolute z-30 rounded-xl p-2.5 w-[230px] text-[11.5px] space-y-1"
          style={{
            left: Math.min(hoverPlot.x + 14, 680),
            top: Math.max(hoverPlot.y - 18, 12),
          }}
        >
          <div className="font-bold text-[#1d1d1f] flex items-center justify-between">
            <span className="truncate">{hoverPlot.plot.name}</span>
            <span className="text-[10px] px-1.5 py-0.2 rounded bg-[#0071e3]/12 text-[#0071e3]">
              #{hoverPlot.plot.plot_id}
            </span>
          </div>
          <div className="grid grid-cols-2 gap-x-2 gap-y-0.5 text-[11px] text-[#515154]">
            <span>建筑栋数: {hoverPlot.plot.bldg_count || 0} 栋</span>
            <span>容积率: {Number(hoverPlot.plot.far || 0).toFixed(2)}</span>
            <span>
              建筑密度: {(Number(hoverPlot.plot.bcr || 0) * 100).toFixed(1)}%
            </span>
            <span>
              绿视率: {(Number(hoverPlot.plot.gvi_mean || 0) * 100).toFixed(1)}%
            </span>
            <span>
              POI密度: {Number(hoverPlot.plot.poi_density || 0).toFixed(1)}
            </span>
            <span>
              句法整合: {Number(hoverPlot.plot.syntax_int_mean || 0).toFixed(2)}
            </span>
          </div>
          <div className="text-[10px] text-[#0071e3] font-semibold pt-0.5">
            点击地块同步联动右侧多维诊断雷达与指标排行
          </div>
        </div>
      )}

      {/* Bottom-Right DepthMapX & Solar Legend Pill */}
      <div className="ud-glass-panel absolute bottom-3 right-12 z-20 rounded-xl px-3 py-1.5 flex items-center gap-3 text-[11px] text-[#1d1d1f]">
        <div className="flex items-center gap-1.5">
          <span className="font-semibold text-[#515154]">句法色阶:</span>
          <span className="w-16 h-2 rounded-full bg-gradient-to-r from-[#2563eb] via-[#22c55e] to-[#ef4444]" />
          <span className="text-[10px] text-[#515154]">低 → 高</span>
        </div>
        <div className="h-3 w-[1px] bg-black/10" />
        <div className="text-[10.5px] text-[#515154]">
          太阳高度角 {solarState.altitudeDeg}° · GPU实时阴影
        </div>
        <div className="h-3 w-[1px] bg-black/10" />
        <div
          className="text-[10.5px] font-semibold text-[#0071e3] tabular-nums"
          title={
            unlockFpsActive
              ? "已解除 VSync 帧率上限（菜单栏「性能与渲染」可切换）"
              : "跟随显示器原生刷新率同步（菜单栏「性能与渲染」可解除 VSync 封顶）"
          }
        >
          {liveFps} FPS {unlockFpsActive ? "· 无上限" : "· 原生刷"}
        </div>
      </div>
    </div>
  );
};

export default SpatialMap3D;

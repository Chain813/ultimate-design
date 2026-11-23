import React, { useEffect } from "react";
import { AppShell } from "./components/AppShell";
import { ensureRuntimeInitialized } from "./services/apiClient";
import { useStudioStore } from "./store/useStudioStore";
import { HomeView } from "./views/HomeView";
import { Workbench01View } from "./views/Workbench01View";
import { Workbench02View } from "./views/Workbench02View";
import { Workbench03View } from "./views/Workbench03View";
import { DatavPopoutView } from "./views/DatavPopoutView";

export const App: React.FC = () => {
  const {
    activeRoute,
    setActiveRoute,
    copilotOpen,
    setCopilotOpen,
    setSettingsOpen,
    refreshSystemHud,
    refreshFusedPlots,
    refreshJobs,
  } = useStudioStore();

  useEffect(() => {
    const syncRouteFromHash = () => {
      const hash = window.location.hash || "";
      if (hash.startsWith("#/datav-popout")) {
        setActiveRoute("datav-popout", "datav");
      } else if (hash.startsWith("#/wb1")) {
        setActiveRoute("wb1");
      } else if (hash.startsWith("#/wb2")) {
        setActiveRoute("wb2");
      } else if (hash.startsWith("#/wb3")) {
        setActiveRoute("wb3");
      } else if (hash.startsWith("#/home")) {
        setActiveRoute("home");
      }
    };

    syncRouteFromHash();
    window.addEventListener("hashchange", syncRouteFromHash);

    const unsubscribeMenu = window.udDesktop?.onMenuCommand?.((cmd) => {
      if (cmd.command === "navigate" && cmd.route) {
        setActiveRoute(cmd.route, cmd.subTab as any);
      } else if (cmd.command === "toggle-copilot") {
        setCopilotOpen(!useStudioStore.getState().copilotOpen);
      } else if (cmd.command === "open-settings") {
        setSettingsOpen(true);
      }
    });

    (async () => {
      await ensureRuntimeInitialized();
      await Promise.allSettled([
        refreshSystemHud(),
        refreshFusedPlots(),
        refreshJobs(),
      ]);
    })();

    return () => {
      window.removeEventListener("hashchange", syncRouteFromHash);
      unsubscribeMenu?.();
    };
  }, [setActiveRoute, setCopilotOpen, setSettingsOpen, refreshSystemHud, refreshFusedPlots, refreshJobs, copilotOpen]);

  if (
    activeRoute === "datav-popout" ||
    (typeof window !== "undefined" &&
      (window.location.hash || "").startsWith("#/datav-popout"))
  ) {
    return <DatavPopoutView />;
  }

  return (
    <AppShell>
      {activeRoute === "home" && <HomeView />}
      {activeRoute === "wb1" && <Workbench01View />}
      {activeRoute === "wb2" && <Workbench02View />}
      {activeRoute === "wb3" && <Workbench03View />}
    </AppShell>
  );
};

export default App;

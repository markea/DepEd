// DepEd NetPulse Interactive Prototype Client-Side Application
// Controls 5 Showcase Tabs, Chart.js Dual-Probe Curves, Bilingual AI Q&A, and HITL Approvals

let dualProbeChartInstance = null;
let nlChartInstance = null;
let activeSchoolId = "104512";
let activeMemoViolationId = null;

// Geospatial Map State (Google Maps Platform)
let phMap = null;
let googleHeatmapLayer = null;
let googleMarkers = [];
let googleInfoWindow = null;
let mapDataFeatures = [];
let activeMapFilter = "ALL";
let activeMapLayerMode = "heat"; // 'heat' or 'pins'

// Executive Light theme map styles for Google Maps (DepEd Cartography)
const GOOGLE_MAPS_LIGHT_STYLE = [
  { elementType: "geometry", stylers: [{ color: "#F8FAFC" }] },
  { elementType: "labels.text.fill", stylers: [{ color: "#334155" }] },
  { elementType: "labels.text.stroke", stylers: [{ color: "#FFFFFF" }, { weight: 2 }] },
  { featureType: "administrative.country", elementType: "geometry.stroke", stylers: [{ color: "#0038A8" }, { weight: 1.5 }] },
  { featureType: "administrative.province", elementType: "geometry.stroke", stylers: [{ color: "#94A3B8" }, { weight: 0.8 }] },
  { featureType: "landscape", elementType: "geometry", stylers: [{ color: "#F1F5F9" }] },
  { featureType: "poi", elementType: "geometry", stylers: [{ color: "#E2E8F0" }] },
  { featureType: "poi", elementType: "labels.text", stylers: [{ visibility: "off" }] },
  { featureType: "road", elementType: "geometry", stylers: [{ color: "#FFFFFF" }] },
  { featureType: "road.highway", elementType: "geometry", stylers: [{ color: "#CBD5E1" }] },
  { featureType: "water", elementType: "geometry", stylers: [{ color: "#DCEEFE" }] },
  { featureType: "water", elementType: "labels.text.fill", stylers: [{ color: "#0284C7" }] }
];

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  initRoleSwitcher();
  loadGoogleMapsAndInit();
  loadNationalSummary();
  loadDivisionWatchlist();
  loadSchoolPortal(activeSchoolId);
  loadGovernanceDashboard();
  initSimulator();
  initConversationalPills();
});

// Tab Navigation
function initTabs() {
  const tabBtns = document.querySelectorAll(".tab-btn");
  const tabContents = document.querySelectorAll(".tab-content");

  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      tabBtns.forEach(b => b.classList.remove("active"));
      tabContents.forEach(c => c.classList.add("hidden"));

      btn.classList.add("active");
      const targetId = btn.getAttribute("data-tab");
      document.getElementById(targetId).classList.remove("hidden");

      if (targetId === "tab1" && phMap && typeof google !== "undefined") {
        setTimeout(() => google.maps.event.trigger(phMap, "resize"), 150);
      }

      if (targetId === "tab3" && dualProbeChartInstance) {
        dualProbeChartInstance.resize();
      }
    });
  });
}

// Role Switcher Simulator
function initRoleSwitcher() {
  const select = document.getElementById("rbacRoleSelect");
  select.addEventListener("change", (e) => {
    const val = e.target.value;
    if (val === "tier1") {
      document.querySelector('[data-tab="tab1"]').click();
      showToast("Switched to Tier 1: Central Office Executive (National Scope)");
    } else if (val === "tier2") {
      document.querySelector('[data-tab="tab2"]').click();
      showToast("Switched to Tier 2: Division Superintendent (SDO Scope)");
    } else if (val === "tier3") {
      document.querySelector('[data-tab="tab3"]').click();
      showToast("Switched to Tier 3: School Principal Portal ($0 BI Cost)");
    }
  });
}

// Toast Helper
function showToast(msg) {
  const toast = document.getElementById("toastBox");
  document.getElementById("toastMessage").innerText = msg;
  toast.style.display = "block";
  setTimeout(() => { toast.style.display = "none"; }, 3500);
}

// ==================== GEOSPATIAL MAP & GOOGLE MAPS PLATFORM ====================
let googleMapsLoadingPromise = null;

function loadGoogleMapsAndInit() {
  if (phMap) return;
  if (typeof google !== "undefined" && google.maps) {
    initMap();
    return;
  }
  if (!googleMapsLoadingPromise) {
    googleMapsLoadingPromise = fetch("/api/v1/config/maps-key")
      .then(res => res.json())
      .then(data => {
        return new Promise((resolve, reject) => {
          const script = document.createElement("script");
          script.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(data.maps_api_key)}&libraries=visualization&v=3.64`;
          script.async = true;
          script.onload = () => {
            initMap();
            resolve();
          };
          script.onerror = reject;
          document.head.appendChild(script);
        });
      })
      .catch(err => {
        console.error("Failed to load Google Maps API:", err);
      });
  }
}

function initMap() {
  if (phMap) return;

  const mapEl = document.getElementById("phConnectivityMap");
  if (!mapEl) return;

  if (typeof google === "undefined" || !google.maps) {
    loadGoogleMapsAndInit();
    return;
  }

  // Center on Philippines Archipelago: [12.8797, 121.7740], zoom 6
  phMap = new google.maps.Map(mapEl, {
    center: { lat: 12.8797, lng: 121.7740 },
    zoom: 6,
    styles: GOOGLE_MAPS_LIGHT_STYLE,
    mapTypeControl: true,
    mapTypeControlOptions: {
      style: google.maps.MapTypeControlStyle.HORIZONTAL_BAR,
      position: google.maps.ControlPosition.TOP_RIGHT,
    },
    streetViewControl: false,
    fullscreenControl: true,
    zoomControl: true,
  });

  googleInfoWindow = new google.maps.InfoWindow();

  // Map Filter Buttons
  const filterBtns = document.querySelectorAll(".map-filter-btn");
  filterBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      filterBtns.forEach(b => {
        b.classList.remove("bg-blue-600", "text-white", "active");
        b.classList.add("text-slate-300");
      });
      btn.classList.remove("text-slate-300");
      btn.classList.add("bg-blue-600", "text-white", "active");
      activeMapFilter = btn.getAttribute("data-issue");
      loadMapData();
    });
  });

  // Layer Mode Toggles
  const btnHeat = document.getElementById("btnLayerHeat");
  const btnPins = document.getElementById("btnLayerPins");

  if (btnHeat && btnPins) {
    btnHeat.addEventListener("click", () => {
      activeMapLayerMode = "heat";
      btnHeat.className = "px-2.5 py-1 rounded text-xs font-semibold bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 flex items-center gap-1";
      btnPins.className = "px-2.5 py-1 rounded text-xs font-semibold text-slate-400 hover:text-white flex items-center gap-1";
      renderMapLayers();
      showToast("Switched to Google Maps Heat Density Cloud view");
    });

    btnPins.addEventListener("click", () => {
      activeMapLayerMode = "pins";
      btnPins.className = "px-2.5 py-1 rounded text-xs font-semibold bg-sky-500/20 text-sky-400 border border-sky-500/30 flex items-center gap-1";
      btnHeat.className = "px-2.5 py-1 rounded text-xs font-semibold text-slate-400 hover:text-white flex items-center gap-1";
      renderMapLayers();
      showToast("Switched to Individual School Pins & Diagnostics view");
    });
  }

  loadMapData();
}

async function loadMapData() {
  try {
    const url = `/api/v1/schools/map-issues?issue_type=${activeMapFilter}`;
    const res = await fetch(url);
    const data = await res.json();
    mapDataFeatures = data.features || [];

    const visibleEl = document.getElementById("mapVisibleCount");
    if (visibleEl) visibleEl.innerText = data.filtered_count;

    renderMapLayers();
  } catch (err) {
    console.error("Error loading map issues data:", err);
  }
}

function renderMapLayers() {
  if (!phMap || typeof google === "undefined") return;

  // Clear existing HeatmapLayer
  if (googleHeatmapLayer) {
    try {
      googleHeatmapLayer.setMap(null);
    } catch (e) {}
    googleHeatmapLayer = null;
  }

  // Clear existing Markers & Circles
  googleMarkers.forEach(m => {
    try {
      m.setMap(null);
    } catch (e) {}
  });
  googleMarkers = [];

  if (activeMapLayerMode === "heat") {
    // 1. Native Google Maps HeatmapLayer
    const heatData = mapDataFeatures
      .filter(f => f.latitude && f.longitude)
      .map(f => {
        const rawWeight = (f.heat_weight != null ? f.heat_weight : 0.6);
        return {
          location: new google.maps.LatLng(f.latitude, f.longitude),
          weight: Math.max(1, rawWeight * 12)
        };
      });

    try {
      if (google.maps.visualization && typeof google.maps.visualization.HeatmapLayer === "function") {
        googleHeatmapLayer = new google.maps.visualization.HeatmapLayer({
          data: heatData,
          map: phMap,
          radius: 55,
          maxIntensity: 6,
          dissipating: true,
          opacity: 0.85,
          gradient: [
            "rgba(0, 0, 0, 0)",
            "rgba(56, 189, 248, 0.7)",   // Cyan (Weather/Satellite)
            "rgba(250, 204, 21, 0.85)",  // Yellow (Wi-Fi/Congestion)
            "rgba(249, 115, 22, 0.95)",  // Orange (Throttling)
            "rgba(239, 68, 68, 1.0)"     // Red (Critical Outage)
          ]
        });
      }
    } catch (err) {
      console.warn("Native HeatmapLayer warning:", err);
    }

    // 2. High-Visibility Multi-Tier Thermal Heat Blooms
    // Draws layered thermal gradient halos so the heat map layer is immediately, boldly visible across the entire Philippines map
    mapDataFeatures.forEach(feat => {
      if (!feat.latitude || !feat.longitude) return;
      const isOutage = feat.severity === "CRITICAL";
      const isThrottling = feat.severity === "HIGH";
      const baseColor = feat.badge_color || (isOutage ? "#ef4444" : (isThrottling ? "#f97316" : "#eab308"));

      // Outer thermal heat plume (40km - 65km)
      const outerHalo = new google.maps.Circle({
        strokeWeight: 0,
        fillColor: baseColor,
        fillOpacity: isOutage ? 0.35 : (isThrottling ? 0.28 : 0.20),
        map: phMap,
        center: { lat: feat.latitude, lng: feat.longitude },
        radius: isOutage ? 65000 : (isThrottling ? 45000 : 35000),
        clickable: false
      });
      googleMarkers.push(outerHalo);

      // Mid-layer thermal core (20km - 32km)
      const midHalo = new google.maps.Circle({
        strokeWeight: 0,
        fillColor: baseColor,
        fillOpacity: isOutage ? 0.55 : (isThrottling ? 0.45 : 0.35),
        map: phMap,
        center: { lat: feat.latitude, lng: feat.longitude },
        radius: isOutage ? 32000 : (isThrottling ? 22000 : 16000),
        clickable: false
      });
      googleMarkers.push(midHalo);

      // Core clickable hotspot badge
      const coreCircle = new google.maps.Circle({
        strokeColor: "#FFFFFF",
        strokeOpacity: 0.9,
        strokeWeight: 1.5,
        fillColor: baseColor,
        fillOpacity: 0.95,
        map: phMap,
        center: { lat: feat.latitude, lng: feat.longitude },
        radius: isOutage ? 10000 : 7000
      });

      coreCircle.addListener("click", () => {
        googleInfoWindow.setContent(buildSchoolPopupHtml(feat));
        googleInfoWindow.setPosition({ lat: feat.latitude, lng: feat.longitude });
        googleInfoWindow.open(phMap);
      });
      googleMarkers.push(coreCircle);
    });

  } else {
    // Pins mode: high-contrast SVG markers with custom color pins
    mapDataFeatures.forEach(feat => {
      if (!feat.latitude || !feat.longitude) return;

      const marker = new google.maps.Marker({
        position: { lat: feat.latitude, lng: feat.longitude },
        map: phMap,
        title: feat.school_name,
        icon: {
          path: google.maps.SymbolPath.CIRCLE,
          scale: feat.severity === "CRITICAL" ? 10 : 7,
          fillColor: feat.badge_color,
          fillOpacity: 0.95,
          strokeColor: "#FFFFFF",
          strokeWeight: 2,
        }
      });

      marker.addListener("click", () => {
        googleInfoWindow.setContent(buildSchoolPopupHtml(feat));
        googleInfoWindow.open(phMap, marker);
      });

      googleMarkers.push(marker);

      // Contracted CIR radius ring
      const cirRing = new google.maps.Circle({
        strokeColor: feat.badge_color,
        strokeOpacity: 0.7,
        strokeWeight: 1,
        fillColor: feat.badge_color,
        fillOpacity: 0.12,
        map: phMap,
        center: { lat: feat.latitude, lng: feat.longitude },
        radius: Math.max(3000, feat.contracted_dl_mbps * 120),
        clickable: false
      });
      googleMarkers.push(cirRing);
    });
  }
}

function buildSchoolPopupHtml(feat) {
  const speedColor = feat.measured_dl_mbps < 50 ? "text-red-600 font-bold" : "text-emerald-700 font-bold";

  return `
    <div class="p-3.5 text-xs bg-white text-slate-800 rounded-lg min-w-[280px] border border-slate-200 shadow-xl">
      <div class="flex items-start justify-between gap-2 border-b border-slate-200 pb-2 mb-2">
        <div>
          <div class="font-bold text-slate-900 text-sm">${feat.school_name}</div>
          <div class="text-[11px] text-slate-500 font-medium">${feat.division_name} &bull; ${feat.region_id}</div>
        </div>
        <span class="text-[10px] px-1.5 py-0.5 rounded font-mono font-bold whitespace-nowrap" style="background:${feat.badge_color}18; color:${feat.badge_color}; border: 1px solid ${feat.badge_color}">
          ${feat.severity}
        </span>
      </div>

      <div class="space-y-1.5 text-slate-600">
        <div class="flex justify-between">
          <span class="text-slate-500">BEIS School ID:</span>
          <span class="font-mono font-semibold text-slate-900">${feat.school_id}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-slate-500">Assigned Provider:</span>
          <span class="font-semibold text-[#0038A8]">${feat.isp_name}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-slate-500">Speed (Actual / CIR):</span>
          <span class="font-mono ${speedColor}">${feat.measured_dl_mbps} / ${feat.contracted_dl_mbps} Mbps</span>
        </div>
        <div class="flex justify-between">
          <span class="text-slate-500">Contract Compliance:</span>
          <span class="font-mono font-bold ${feat.compliance_pct < 70 ? 'text-red-600' : 'text-emerald-700'}">${feat.compliance_pct}%</span>
        </div>
        <div class="pt-1 border-t border-slate-100">
          <div class="text-slate-400 text-[10px] font-semibold uppercase">Diagnostic Category:</div>
          <div class="font-semibold text-slate-800 mt-0.5">${feat.issue_label}</div>
        </div>
        ${feat.is_selective_throttling ? '<div class="text-[10px] text-red-800 bg-red-50 p-1.5 rounded border border-red-200 font-medium">🚨 Public speedtest shows ' + feat.public_dl_mbps + ' Mbps while DepEd Cloud is throttled.</div>' : ''}
      </div>

      <div class="mt-3 pt-2 border-t border-slate-200 flex justify-end">
        <button onclick="selectSchool('${feat.school_id}')" class="px-3 py-1.5 rounded bg-[#0038A8] hover:bg-[#002266] text-white font-semibold text-[11px] flex items-center gap-1.5 transition shadow-sm cursor-pointer">
          <i class="fa-solid fa-arrow-up-right-from-square"></i> Open School Portal ($0 BI)
        </button>
      </div>
    </div>
  `;
}

function zoomToHotspot(lat, lng, zoom, regionId) {
  if (!phMap || typeof google === "undefined") return;
  phMap.panTo({ lat, lng });
  phMap.setZoom(zoom);
  showToast(`Zoomed Google Map to ${regionId} Hotspot Cluster`);
}

function resetMapView() {
  if (!phMap || typeof google === "undefined") return;
  phMap.panTo({ lat: 12.8797, lng: 121.7740 });
  phMap.setZoom(6);
  showToast("Reset Google Map to National Archipelago view");
}

// Tab 1: Load National Summary & 17 Regions
async function loadNationalSummary() {
  try {
    const res = await fetch("/api/v1/national/summary");
    const data = await res.json();

    // KPIs
    document.getElementById("kpiTotalSchools").innerHTML = `${data.kpis.online_schools.toLocaleString()} <span class="text-xs font-normal text-slate-400">/ ${data.kpis.total_schools.toLocaleString()}</span>`;
    document.getElementById("kpiUptime").innerText = `${data.kpis.uptime_pct}%`;
    document.getElementById("kpiCirCompliance").innerText = `${data.kpis.national_cir_compliance_pct}%`;
    document.getElementById("kpiTotalRebates").innerText = `₱${data.kpis.total_monthly_sla_rebates_php.toLocaleString(undefined, {minimumFractionDigits: 2})}`;

    // 17-Region Heatmap Grid
    const grid = document.getElementById("regionalGrid");
    grid.innerHTML = data.regions.map(r => {
      let badgeClass = "badge-compliant";
      if (r.compliance_pct < 70 || r.active_cluster_outage) badgeClass = "badge-danger";
      else if (r.compliance_pct < 85) badgeClass = "badge-warning";

      return `
        <div class="p-2.5 rounded-lg border border-slate-200 bg-white hover:border-[#0038A8] hover:shadow-md transition cursor-pointer" onclick="filterByRegion('${r.region_id}')">
          <div class="flex justify-between items-start">
            <span class="font-bold text-xs text-slate-900">${r.region_id}</span>
            <span class="text-[10px] px-1.5 py-0.5 rounded font-mono ${badgeClass}">${r.compliance_pct}%</span>
          </div>
          <div class="text-[11px] text-slate-700 font-semibold truncate mt-1">${r.region_name}</div>
          <div class="flex justify-between items-center text-[10px] text-slate-500 mt-2">
            <span>${r.online_schools.toLocaleString()} / ${r.total_schools.toLocaleString()} schools</span>
            <span class="text-[#0038A8] font-mono font-bold">${r.avg_speed_mbps} Mbps</span>
          </div>
          ${r.active_cluster_outage ? '<div class="text-[9px] text-[#CE1126] font-bold mt-1 animate-pulse"><i class="fa-solid fa-triangle-exclamation"></i> Cluster Cut Active</div>' : ''}
        </div>
      `;
    }).join("");

    // ISP SLA & Anti-Gaming Leaderboard
    const tbody = document.getElementById("ispLeaderboardBody");
    tbody.innerHTML = data.isps.map(isp => {
      const isThrottling = isp.selective_throttling_flag;
      return `
        <tr class="hover:bg-slate-50 transition border-b border-slate-100">
          <td class="py-2.5 font-semibold text-slate-800 flex items-center gap-1.5">
            ${isp.isp_name}
            ${isThrottling ? '<span class="text-[9px] bg-red-100 text-red-800 border border-red-300 px-1.5 py-0.2 rounded font-bold">ANTI-GAMING FLAG</span>' : ''}
          </td>
          <td class="py-2.5 text-center font-mono ${isp.deped_anchor_avg_pct < 50 ? 'text-[#CE1126] font-bold' : 'text-emerald-700 font-semibold'}">${isp.deped_anchor_avg_pct}%</td>
          <td class="py-2.5 text-center font-mono text-slate-600">${isp.public_ref_avg_pct}%</td>
          <td class="py-2.5 text-right font-mono text-[#CE1126] font-bold">₱${isp.monthly_rebates_eligible_php.toLocaleString(undefined, {minimumFractionDigits: 2})}</td>
        </tr>
      `;
    }).join("");

  } catch (err) {
    console.error("Error loading national summary:", err);
  }
}

function filterByRegion(regionId) {
  document.querySelector('[data-tab="tab2"]').click();
  showToast(`Filtered Division drilldown for ${regionId}`);
}

// Tab 2: Load Division Watchlist & Enrollment Command
async function loadDivisionWatchlist() {
  try {
    const res = await fetch("/api/v1/divisions");
    const data = await res.json();

    const tbody = document.getElementById("divisionWatchlistBody");
    tbody.innerHTML = data.schools_watchlist.map(s => {
      let badge = '<span class="badge-compliant px-2 py-0.5 rounded text-[10px]">COMPLIANT</span>';
      if (s.archetype === "ISP_SELECTIVE_THROTTLING") {
        badge = '<span class="badge-danger px-2 py-0.5 rounded text-[10px]">SELECTIVE THROTTLING</span>';
      } else if (s.archetype === "LOCAL_WIFI_BOTTLENECK") {
        badge = '<span class="badge-exempt px-2 py-0.5 rounded text-[10px]">LOCAL WI-FI EXEMPT</span>';
      } else if (s.archetype === "REGIONAL_FIBER_CUT") {
        badge = '<span class="badge-danger px-2 py-0.5 rounded text-[10px]">CLUSTER FIBER CUT</span>';
      } else if (s.archetype === "RURAL_SATELLITE_WEATHER") {
        badge = '<span class="badge-warning px-2 py-0.5 rounded text-[10px]">SATELLITE RAIN FADE</span>';
      }

      return `
        <tr class="hover:bg-slate-50 cursor-pointer border-b border-slate-100 transition" onclick="selectSchool('${s.school_id}')">
          <td class="py-2.5 font-bold text-slate-900">${s.school_name} <br><span class="text-[10px] font-normal text-slate-500 font-mono">${s.school_id}</span></td>
          <td class="py-2.5 text-slate-700">${s.division_name} <br><span class="text-[10px] text-slate-500 font-semibold">${s.region_id}</span></td>
          <td class="py-2.5 text-slate-700 font-mono text-[11px]">${s.archetype === 'LOCAL_WIFI_BOTTLENECK' ? 'WIFI (-86 dBm)' : 'ETHERNET (1ms)'}</td>
          <td class="py-2.5 font-mono font-bold ${s.contracted_dl_mbps < 50 ? 'text-amber-600' : 'text-emerald-700'}">${s.contracted_dl_mbps} Mbps</td>
          <td class="py-2.5">${badge}</td>
        </tr>
      `;
    }).join("");

    // 1-Click Enrollment Command Generator
    document.getElementById("btnGenerateEnroll").addEventListener("click", async () => {
      const schoolId = document.getElementById("enrollSchoolSelect").value;
      const os = document.querySelector('input[name="enrollOS"]:checked').value;
      const cmdRes = await fetch("/api/v1/devices/enrollment-command", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: json.stringify({ school_id: schoolId, target_os: os })
      });
      const cmdData = await cmdRes.json();
      document.getElementById("enrollCommandText").innerText = cmdData.command;
      document.getElementById("enrollCommandBox").classList.remove("hidden");
      showToast(`Generated enrollment bootstrap token for School ${schoolId}`);
    });

  } catch (err) {
    console.error("Error loading division watchlist:", err);
  }
}

function selectSchool(schoolId) {
  activeSchoolId = schoolId;
  document.getElementById("portalSchoolSelect").value = schoolId;
  document.querySelector('[data-tab="tab3"]').click();
  loadSchoolPortal(schoolId);
}

// Tab 3: School Principal Portal ($0 BI Seat License View)
document.getElementById("portalSchoolSelect").addEventListener("change", (e) => {
  activeSchoolId = e.target.value;
  loadSchoolPortal(activeSchoolId);
});

document.getElementById("btnOpenCert").addEventListener("click", () => {
  window.open(`/static/certificate.html?school_id=${activeSchoolId}`, "_blank");
});

async function loadSchoolPortal(schoolId) {
  try {
    const res = await fetch(`/api/v1/schools/${schoolId}`);
    const data = await res.json();
    const meta = data.school_metadata;
    const latest = data.latest_telemetry;
    const diag = data.bilingual_diagnosis;

    document.getElementById("schoolSubtitle").innerText = `${meta.region_name} | ${meta.division_name} | Assigned ISP: ${meta.isp_name} (${meta.contracted_dl_mbps} Mbps Fiber)`;

    // Local Hop Badge
    const hopVerdict = document.getElementById("localHopVerdict");
    const hopMetrics = document.getElementById("localHopMetrics");

    if (latest.connection_medium === "WIFI" && latest.wifi_rssi_dbm <= -75) {
      hopVerdict.innerHTML = '<span class="text-amber-400"><i class="fa-solid fa-triangle-exclamation"></i> WEAK CLASSROOM WI-FI DETECTED</span> <span class="badge-exempt px-2 py-0.5 rounded text-[10px]">ISP EXEMPT</span>';
      hopMetrics.innerHTML = `
        <span class="bg-slate-800 px-2 py-1 rounded border border-slate-700 text-slate-300">Medium: <strong>WIFI (${latest.wifi_rssi_dbm} dBm)</strong></span>
        <span class="bg-slate-800 px-2 py-1 rounded border border-slate-700 text-amber-400">Router Ping: <strong>${latest.local_gateway_ping_ms} ms</strong></span>
      `;
    } else {
      hopVerdict.innerHTML = '<span class="text-emerald-400"><i class="fa-solid fa-circle-check"></i> LOCAL NETWORK VERIFIED 100% HEALTHY</span> <span class="badge-compliant px-2 py-0.5 rounded text-[10px]">CONFIRMED WAN ISSUE</span>';
      hopMetrics.innerHTML = `
        <span class="bg-slate-800 px-2 py-1 rounded border border-slate-700 text-slate-300">Medium: <strong>ETHERNET (RJ45)</strong></span>
        <span class="bg-slate-800 px-2 py-1 rounded border border-slate-700 text-emerald-400">Router Ping: <strong>${latest.local_gateway_ping_ms || 1.2} ms</strong></span>
        <span class="bg-slate-800 px-2 py-1 rounded border border-slate-700 text-emerald-400">Router Loss: <strong>0.0%</strong></span>
      `;
    }

    // Bilingual Diagnostic Card
    document.getElementById("diagEnText").innerText = diag.diagnosis_en;
    document.getElementById("diagTlText").innerText = diag.diagnosis_tl;

    // Dual-Probe Chart.js Curve
    renderDualProbeChart(data.time_series_records, meta.contracted_dl_mbps);

  } catch (err) {
    console.error("Error loading school portal:", err);
  }
}

function renderDualProbeChart(records, contractedSpeed) {
  const ctx = document.getElementById("dualProbeChart").getContext("2d");
  if (dualProbeChartInstance) {
    dualProbeChartInstance.destroy();
  }

  const labels = records.map(r => `${r.test_date.substring(5)} ${r.test_hour}:00`);
  const anchorSpeeds = records.map(r => r.deped_anchor_dl_mbps);
  const publicSpeeds = records.map(r => r.public_ref_dl_mbps);
  const contractedBaseline = records.map(() => contractedSpeed);

  dualProbeChartInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Contracted CIR Baseline (Mbps)",
          data: contractedBaseline,
          borderColor: "#94A3B8",
          borderDash: [6, 6],
          borderWidth: 2,
          pointRadius: 0,
          fill: false,
        },
        {
          label: "Public Reference Speedtest (Mbps)",
          data: publicSpeeds,
          borderColor: "#38BDF8",
          backgroundColor: "rgba(56, 189, 248, 0.05)",
          borderWidth: 2,
          pointRadius: 2,
          fill: false,
        },
        {
          label: "DepEd Cloud Anchor Speed (Mbps)",
          data: anchorSpeeds,
          borderColor: "#EF4444",
          backgroundColor: "rgba(239, 68, 68, 0.15)",
          borderWidth: 2.5,
          pointRadius: 3,
          fill: true,
        },
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { labels: { color: "#334155", font: { size: 11, weight: "bold" } } },
        tooltip: {
          callbacks: {
            footer: (items) => {
              const diff = (items[1]?.raw || 0) - (items[2]?.raw || 0);
              return diff > 30 ? `⚠️ Throttling Gap: ${diff.toFixed(1)} Mbps` : '';
            }
          }
        }
      },
      scales: {
        x: { ticks: { color: "#475569", maxTicksLimit: 10 }, grid: { color: "rgba(0,0,0,0.06)" } },
        y: { ticks: { color: "#475569" }, grid: { color: "rgba(0,0,0,0.08)" }, title: { display: true, text: "Mbps", color: "#334155" } }
      }
    }
  });
}

// Tab 4: Gemini Enterprise Hub (Bilingual Conversational Analytics + HITL Actions)
function initConversationalPills() {
  document.querySelectorAll(".nl-pill").forEach(pill => {
    pill.addEventListener("click", () => {
      document.getElementById("nlQueryInput").value = pill.getAttribute("data-query");
      executeQuery();
    });
  });

  document.getElementById("btnExecuteQuery").addEventListener("click", executeQuery);
  document.getElementById("nlQueryInput").addEventListener("keypress", (e) => {
    if (e.key === "Enter") executeQuery();
  });
}

async function executeQuery() {
  const input = document.getElementById("nlQueryInput");
  const prompt = input.value.trim();
  if (!prompt) return;

  const btn = document.getElementById("btnExecuteQuery");
  btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Reasoning...';

  try {
    const res = await fetch("/api/v1/gemini/conversational-query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt })
    });
    const data = await res.json();

    document.getElementById("nlResultBox").classList.remove("hidden");
    document.getElementById("nlAnswerText").innerHTML = data.conversational_answer.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    document.getElementById("nlSqlText").innerText = data.generated_sql;

    if (data.chart_data) {
      renderNLChart(data.chart_data);
    }
  } catch (err) {
    console.error("Error executing NL query:", err);
  } finally {
    btn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Execute Query';
  }
}

function renderNLChart(chartData) {
  const ctx = document.getElementById("nlChart").getContext("2d");
  if (nlChartInstance) nlChartInstance.destroy();

  nlChartInstance = new Chart(ctx, {
    type: "bar",
    data: chartData,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { labels: { color: "#334155", font: { weight: "bold" } } } },
      scales: {
        x: { ticks: { color: "#475569" }, grid: { display: false } },
        y: { ticks: { color: "#475569" }, grid: { color: "rgba(0,0,0,0.06)" } }
      }
    }
  });
}

async function loadGovernanceDashboard() {
  try {
    const res = await fetch("/api/v1/governance/dashboard");
    const data = await res.json();

    // Zero-Touch Technical Tickets Feed
    const feed = document.getElementById("zeroTouchFeed");
    feed.innerHTML = data.zero_touch_tickets.map(t => `
      <div class="p-3 bg-white border border-slate-200 rounded-lg space-y-1.5 shadow-sm">
        <div class="flex justify-between items-start">
          <span class="font-bold text-xs text-slate-900">${t.title}</span>
          <span class="text-[9px] bg-red-100 text-red-800 border border-red-300 px-1.5 py-0.5 rounded font-mono font-bold">${t.severity}</span>
        </div>
        <div class="text-[11px] text-slate-600">${t.description}</div>
        <div class="text-[10px] text-purple-700 font-medium">${t.gemini_diagnosis}</div>
        <div class="flex justify-between items-center text-[9px] text-slate-500 pt-1 border-t border-slate-100">
          <span>Ticket: <strong class="text-slate-800 font-mono">${t.ticket_id}</strong></span>
          <span class="text-emerald-700 font-semibold"><i class="fa-solid fa-paper-plane mr-1"></i> Dispatched to Gmail & Chat</span>
        </div>
      </div>
    `).join("");

    // HITL Rebate Approval Queue
    const queue = document.getElementById("hitlRebateQueue");
    queue.innerHTML = data.hitl_rebate_queue.map(v => {
      const isApproved = v.hitl_approval_state === "APPROVED_FOR_REBATE";
      return `
        <div class="p-3 bg-white border ${isApproved ? 'border-emerald-300 bg-emerald-50/40' : 'border-amber-300 bg-amber-50/20'} rounded-lg space-y-2 shadow-sm">
          <div class="flex justify-between items-start">
            <div>
              <div class="font-bold text-xs text-slate-900">${v.school_name} (${v.school_id})</div>
              <div class="text-[10px] text-slate-500">ISP: <strong>${v.isp_name}</strong> | Breach: <strong>${v.consecutive_breach_days} Consecutive Days</strong></div>
            </div>
            <span class="text-xs font-mono font-black text-[#CE1126]">₱${v.calculated_rebate_php.toLocaleString(undefined, {minimumFractionDigits: 2})}</span>
          </div>
          <p class="text-[11px] text-slate-700 leading-snug">${v.gemini_diagnostic_en}</p>
          <div class="flex justify-between items-center pt-1.5 border-t border-slate-100 text-xs">
            <button class="text-[#0038A8] hover:underline text-[11px] font-semibold" onclick="inspectMemo('${v.violation_id}')">
              <i class="fa-solid fa-file-lines mr-1"></i> Inspect COA Memo
            </button>
            ${isApproved ? 
              `<span class="text-emerald-700 text-[11px] font-bold flex items-center gap-1"><i class="fa-solid fa-circle-check"></i> Approved by ${v.approved_by_human_email}</span>` : 
              `<button class="bg-[#CE1126] hover:bg-red-700 text-white font-bold px-3 py-1 rounded text-[11px] transition shadow-sm cursor-pointer" onclick="approveRebate('${v.violation_id}')">
                <i class="fa-solid fa-check mr-1"></i> Approve Deduction (HITL)
              </button>`
            }
          </div>
        </div>
      `;
    }).join("");

  } catch (err) {
    console.error("Error loading governance dashboard:", err);
  }
}

async function inspectMemo(violationId) {
  activeMemoViolationId = violationId;
  const res = await fetch("/api/v1/governance/dashboard");
  const data = await res.json();
  const viol = data.hitl_rebate_queue.find(v => v.violation_id === violationId);
  if (viol) {
    document.getElementById("memoModalContent").innerText = viol.draft_dispute_memo_md;
    document.getElementById("memoModal").classList.remove("hidden");
  }
}

document.getElementById("btnCloseMemo").addEventListener("click", () => document.getElementById("memoModal").classList.add("hidden"));
document.getElementById("btnModalClose").addEventListener("click", () => document.getElementById("memoModal").classList.add("hidden"));
document.getElementById("btnModalApprove").addEventListener("click", () => {
  if (activeMemoViolationId) {
    approveRebate(activeMemoViolationId);
    document.getElementById("memoModal").classList.add("hidden");
  }
});

async function approveRebate(violationId) {
  try {
    const res = await fetch(`/api/v1/governance/rebates/${violationId}/approve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ approver_email: "dito.cavite@deped.gov.ph" })
    });
    const result = await res.json();
    showToast(result.message);
    loadGovernanceDashboard();
    loadNationalSummary();
  } catch (err) {
    console.error("Error approving rebate:", err);
  }
}

// Tab 5: Live 47k Simulator
function initSimulator() {
  document.querySelectorAll(".sim-btn").forEach(btn => {
    btn.addEventListener("click", async () => {
      const scenario = btn.getAttribute("data-scenario");
      const statusPill = document.getElementById("simStatusPill");
      statusPill.innerText = "PROCESSING...";
      statusPill.className = "text-amber-400 font-mono animate-pulse";

      try {
        const res = await fetch("/api/v1/simulator/trigger", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ scenario_id: scenario })
        });
        const data = await res.json();
        document.getElementById("simConsoleOutput").innerText = JSON.stringify(data, null, 2);
        statusPill.innerText = "SUCCESS (200 OK)";
        statusPill.className = "text-emerald-400 font-mono";

        showToast(data.message || "Simulated telemetry event processed.");
        loadNationalSummary();
        loadDivisionWatchlist();
        loadSchoolPortal(activeSchoolId);
      } catch (err) {
        statusPill.innerText = "ERROR";
        statusPill.className = "text-red-400 font-mono";
        console.error("Simulator error:", err);
      }
    });
  });
}

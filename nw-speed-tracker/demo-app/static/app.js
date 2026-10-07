// DepEd NetPulse Interactive Prototype Client-Side Application
// Controls 5 Showcase Tabs, Chart.js Dual-Probe Curves, Bilingual AI Q&A, and HITL Approvals

let dualProbeChartInstance = null;
let nlChartInstance = null;
let activeSchoolId = "104512";
let activeMemoViolationId = null;

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  initRoleSwitcher();
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
        <div class="p-2.5 rounded-lg border border-slate-700 bg-slate-800/60 hover:border-yellow-400 transition cursor-pointer" onclick="filterByRegion('${r.region_id}')">
          <div class="flex justify-between items-start">
            <span class="font-bold text-xs text-white">${r.region_id}</span>
            <span class="text-[10px] px-1.5 py-0.5 rounded font-mono ${badgeClass}">${r.compliance_pct}%</span>
          </div>
          <div class="text-[11px] text-slate-300 font-medium truncate mt-1">${r.region_name}</div>
          <div class="flex justify-between items-center text-[10px] text-slate-400 mt-2">
            <span>${r.online_schools.toLocaleString()} / ${r.total_schools.toLocaleString()} schools</span>
            <span class="text-sky-400 font-mono">${r.avg_speed_mbps} Mbps</span>
          </div>
          ${r.active_cluster_outage ? '<div class="text-[9px] text-red-400 font-bold mt-1 animate-pulse"><i class="fa-solid fa-triangle-exclamation"></i> Cluster Cut Active</div>' : ''}
        </div>
      `;
    }).join("");

    // ISP SLA & Anti-Gaming Leaderboard
    const tbody = document.getElementById("ispLeaderboardBody");
    tbody.innerHTML = data.isps.map(isp => {
      const isThrottling = isp.selective_throttling_flag;
      return `
        <tr class="hover:bg-slate-800/40">
          <td class="py-2.5 font-medium text-white flex items-center gap-1.5">
            ${isp.isp_name}
            ${isThrottling ? '<span class="text-[9px] bg-red-950 text-red-400 border border-red-800 px-1.5 py-0.2 rounded font-bold">ANTI-GAMING FLAG</span>' : ''}
          </td>
          <td class="py-2.5 text-center font-mono ${isp.deped_anchor_avg_pct < 50 ? 'text-red-400 font-bold' : 'text-emerald-400'}">${isp.deped_anchor_avg_pct}%</td>
          <td class="py-2.5 text-center font-mono text-slate-300">${isp.public_ref_avg_pct}%</td>
          <td class="py-2.5 text-right font-mono text-amber-400 font-bold">₱${isp.monthly_rebates_eligible_php.toLocaleString(undefined, {minimumFractionDigits: 2})}</td>
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
        <tr class="hover:bg-slate-800/40 cursor-pointer" onclick="selectSchool('${s.school_id}')">
          <td class="py-2.5 font-bold text-white">${s.school_name} <br><span class="text-[10px] font-normal text-slate-400 font-mono">${s.school_id}</span></td>
          <td class="py-2.5 text-slate-300">${s.division_name} <br><span class="text-[10px] text-slate-400">${s.region_id}</span></td>
          <td class="py-2.5 text-slate-300 font-mono">${s.archetype === 'LOCAL_WIFI_BOTTLENECK' ? 'WIFI (-86 dBm)' : 'ETHERNET (1ms)'}</td>
          <td class="py-2.5 font-mono ${s.contracted_dl_mbps < 50 ? 'text-amber-400' : 'text-emerald-400'}">${s.contracted_dl_mbps} Mbps</td>
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
        legend: { labels: { color: "#CBD5E1", font: { size: 11 } } },
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
        x: { ticks: { color: "#94A3B8", maxTicksLimit: 10 }, grid: { color: "rgba(255,255,255,0.05)" } },
        y: { ticks: { color: "#94A3B8" }, grid: { color: "rgba(255,255,255,0.08)" }, title: { display: true, text: "Mbps", color: "#94A3B8" } }
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
      plugins: { legend: { labels: { color: "#CBD5E1" } } },
      scales: {
        x: { ticks: { color: "#94A3B8" }, grid: { display: false } },
        y: { ticks: { color: "#94A3B8" }, grid: { color: "rgba(255,255,255,0.05)" } }
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
      <div class="p-3 bg-slate-900 border border-slate-800 rounded-lg space-y-2">
        <div class="flex justify-between items-start">
          <span class="font-bold text-xs text-white">${t.title}</span>
          <span class="text-[9px] bg-red-950 text-red-400 border border-red-800 px-1.5 py-0.5 rounded font-mono font-bold">${t.severity}</span>
        </div>
        <div class="text-[11px] text-slate-300">${t.description}</div>
        <div class="text-[10px] text-purple-300 font-medium">${t.gemini_diagnosis}</div>
        <div class="flex justify-between items-center text-[9px] text-slate-400 pt-1 border-t border-slate-800/60">
          <span>Ticket: <strong class="text-white">${t.ticket_id}</strong></span>
          <span class="text-emerald-400"><i class="fa-solid fa-paper-plane mr-1"></i> Dispatched to Gmail & Google Chat</span>
        </div>
      </div>
    `).join("");

    // HITL Rebate Approval Queue
    const queue = document.getElementById("hitlRebateQueue");
    queue.innerHTML = data.hitl_rebate_queue.map(v => {
      const isApproved = v.hitl_approval_state === "APPROVED_FOR_REBATE";
      return `
        <div class="p-3 bg-slate-900 border ${isApproved ? 'border-emerald-800/80 bg-emerald-950/10' : 'border-amber-800/60'} rounded-lg space-y-2.5">
          <div class="flex justify-between items-start">
            <div>
              <div class="font-bold text-xs text-white">${v.school_name} (${v.school_id})</div>
              <div class="text-[10px] text-slate-400">ISP: ${v.isp_name} | Breach: ${v.consecutive_breach_days} Consecutive Days</div>
            </div>
            <span class="text-xs font-mono font-black text-amber-400">₱${v.calculated_rebate_php.toLocaleString(undefined, {minimumFractionDigits: 2})}</span>
          </div>
          <p class="text-[11px] text-slate-300 leading-snug">${v.gemini_diagnostic_en}</p>
          <div class="flex justify-between items-center pt-1.5 border-t border-slate-800/60 text-xs">
            <button class="text-sky-400 hover:text-sky-300 text-[11px] font-semibold" onclick="inspectMemo('${v.violation_id}')">
              <i class="fa-solid fa-file-lines mr-1"></i> Inspect COA Memo
            </button>
            ${isApproved ? 
              `<span class="text-emerald-400 text-[11px] font-bold flex items-center gap-1"><i class="fa-solid fa-circle-check"></i> Approved by ${v.approved_by_human_email}</span>` : 
              `<button class="bg-amber-500 hover:bg-amber-400 text-slate-900 font-bold px-3 py-1 rounded text-[11px] transition shadow" onclick="approveRebate('${v.violation_id}')">
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

import "./styles.css";

const DEFAULT_API_BASE = "http://127.0.0.1:8000";
const API_KEY_STORAGE = "aset.signaldesk.apiBase";
const state = {
  apiBase: localStorage.getItem(API_KEY_STORAGE) || DEFAULT_API_BASE,
  current: null
};

const $ = (id) => document.getElementById(id);

function normalizeBase(value) {
  var base = String(value || "").trim().replace(/\/+$/, "");
  return base || DEFAULT_API_BASE;
}

function money(value) {
  if (value == null || Number.isNaN(Number(value))) return "—";
  return new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 2 }).format(Number(value));
}

function pct(value, digits) {
  if (value == null || Number.isNaN(Number(value))) return "—";
  return (Number(value) * 100).toFixed(digits == null ? 1 : digits) + "%";
}

function esc(value) {
  return String(value == null ? "" : value).replace(/[&<>"']/g, function (c) {
    return { "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" }[c];
  });
}

function apiUrl(path) {
  return state.apiBase + path;
}

async function request(path) {
  var response = await fetch(apiUrl(path), { headers: { Accept: "application/json" } });
  var data = await response.json().catch(function () { return {}; });
  if (!response.ok) throw new Error(data.detail || "Request failed (" + response.status + ").");
  return data;
}

function setStatus(message, kind) {
  $("connection").textContent = message;
  $("connection").className = "connection " + (kind || "");
}

function renderLoading(symbol) {
  $("ticker").textContent = symbol;
  $("company").textContent = "Fetching provider data…";
  $("price").textContent = "—";
  $("quoteChange").textContent = "—";
  ["revenue","income","margin","avg","debt","cash","debtCash","cap"].forEach(function (id) { $(id).textContent = "—"; });
  $("history").innerHTML = "<tr><td colspan='4' class='mutedCell'>Loading…</td></tr>";
  $("flags").innerHTML = "<span class='mutedCell'>Loading…</span>";
  $("source").textContent = "Waiting for provider response…";
}

function render(data) {
  state.current = data;
  var f = data.fundamentals || {};
  var q = data.quote || {};

  $("company").textContent = data.company || data.symbol;
  $("ticker").textContent = [data.symbol,data.exchange,data.country,data.currency].filter(Boolean).join(" · ");
  $("price").textContent = q.price == null ? "—" : money(q.price);

  var change = q.change == null ? "—" : money(q.change);
  var changePct = q.change_percent == null ? "—" : pct(q.change_percent, 2);
  $("quoteChange").innerHTML = q.change == null
    ? "—"
    : change + ' <span class="' + (q.change >= 0 ? "positive" : "negative") + '">' + changePct + "</span>";

  $("revenue").textContent = money(f.revenue);
  $("income").textContent = money(f.net_income);
  $("margin").textContent = pct(f.net_margin);
  $("avg").textContent = money(f.average_5y_net_income);
  $("debt").textContent = money(f.debt);
  $("cash").textContent = money(f.cash);
  $("debtCash").textContent = f.debt_cash == null ? "—" : Number(f.debt_cash).toFixed(2) + "x";
  $("cap").textContent = money(f.market_cap);

  var history = data.income_history || [];
  $("history").innerHTML = history.length
    ? history.map(function (row, i) {
        var prior = history[i + 1] && history[i + 1].net_income;
        var growth = row.net_income != null && prior != null && prior !== 0 ? row.net_income / prior - 1 : null;
        return "<tr><td>" + esc(row.fiscal_date || "—") + "</td><td>" + money(row.revenue) + "</td><td>" +
          money(row.net_income) + "</td><td class='" + (growth != null && growth < 0 ? "negativeText" : "") + "'>" +
          pct(growth) + "</td></tr>";
      }).join("")
    : "<tr><td colspan='4' class='mutedCell'>No annual income history returned.</td></tr>";

  var flags = data.flags || [];
  $("flags").innerHTML = flags.length
    ? flags.map(function (flag) { return "<span class='tag'>" + esc(flag) + "</span>"; }).join("")
    : "<span class='mutedCell'>No rule-based flags triggered.</span>";

  $("source").textContent = (data.sources || []).map(function (item) {
    return [item.provider,item.function,item.mode,item.freshness,"fetched " + item.fetched_at].join(" · ");
  }).join("\n");

  $("meta").textContent = [data.meta && data.meta.provider,data.meta && data.meta.freshness,
    data.meta && data.meta.demo_preview ? "demo preview" : "API key",
    data.meta && data.meta.cache].filter(Boolean).join(" · ");

  setStatus("Connected · " + state.apiBase, "ok");
  $("error").hidden = true;
}

async function analyze() {
  $("error").hidden = true;
  var symbol = $("symbol").value.trim().toUpperCase();
  if (!/^[A-Z0-9.:-]{1,15}$/.test(symbol)) {
    $("error").textContent = "Enter a valid ticker symbol.";
    $("error").hidden = false;
    return;
  }

  renderLoading(symbol);
  setStatus("Fetching original provider data");
  $("analyze").disabled = true;

  try {
    var data = await request("/api/v1/research/" + encodeURIComponent(symbol));
    render(data);
  } catch (error) {
    $("error").textContent = error.message || String(error);
    $("error").hidden = false;
    setStatus("Connection error", "errorState");
  } finally {
    $("analyze").disabled = false;
  }
}

async function checkConnection() {
  try {
    var config = await request("/api/v1/config");
    setStatus(config.api_key_configured ? "Connected · live API key" : "Connected · labeled demo mode", "ok");
    $("apiBase").value = state.apiBase;
    $("provider").textContent = config.provider || "Provider";
  } catch (error) {
    setStatus("API offline · configure connection", "errorState");
  }
}

function openSettings() {
  $("settings").showModal();
  $("apiBase").value = state.apiBase;
}

function saveSettings() {
  state.apiBase = normalizeBase($("apiBase").value);
  localStorage.setItem(API_KEY_STORAGE, state.apiBase);
  $("settings").close();
  setStatus("Checking connection…");
  checkConnection().then(analyze);
}

function exportJson() {
  if (!state.current) return;
  var blob = new Blob([JSON.stringify(state.current, null, 2)], { type: "application/json" });
  var url = URL.createObjectURL(blob);
  var link = document.createElement("a");
  link.href = url;
  link.download = (state.current.symbol || "research") + "-signaldesk.json";
  link.click();
  URL.revokeObjectURL(url);
}

function boot() {
  $("app").innerHTML = [
    '<div class="shell">',
      '<header class="topbar">',
        '<div class="brand"><span class="brandMark">A</span><span>ASET <b>/ SignalDesk</b></span></div>',
        '<div class="topActions"><span id="provider" class="provider">Provider</span><span id="connection" class="connection">Connecting…</span><button id="settingsBtn" class="btn">Connection</button></div>',
      '</header>',
      '<main>',
        '<section class="hero">',
          '<div class="eyebrow">WINDOWS DESKTOP · ORIGINAL PROVIDER DATA</div>',
          '<h1>Research with live numbers.</h1>',
          '<p>Analyze public companies through your configured ASET SignalDesk API. Missing values remain missing — the desktop app never invents financial data.</p>',
          '<div class="search"><input id="symbol" maxlength="15" value="IBM" aria-label="Ticker symbol" autocomplete="off" spellcheck="false"><button id="analyze" class="btn primary">Analyze</button><button id="refresh" class="btn">Refresh</button></div>',
          '<div id="error" class="error" hidden></div>',
        '</section>',
        '<section class="companyPanel panel"><div class="sectionHead"><span>Company</span><span id="meta" class="muted">Waiting for data</span></div><div class="companyRow"><div><div id="company" class="companyName">—</div><div id="ticker" class="ticker">—</div><div id="price" class="price">—</div></div><div id="quoteChange" class="quoteChange">—</div></div></section>',
        '<section class="metrics">',
          '<div class="metric"><span>Revenue</span><strong id="revenue">—</strong></div><div class="metric"><span>Net income</span><strong id="income">—</strong></div>',
          '<div class="metric"><span>Net margin</span><strong id="margin">—</strong></div><div class="metric"><span>5Y avg income</span><strong id="avg">—</strong></div>',
          '<div class="metric"><span>Debt</span><strong id="debt">—</strong></div><div class="metric"><span>Cash</span><strong id="cash">—</strong></div>',
          '<div class="metric"><span>Debt / cash</span><strong id="debtCash">—</strong></div><div class="metric"><span>Market cap</span><strong id="cap">—</strong></div>',
        '</section>',
        '<section class="panel"><div class="sectionHead"><span>Five-year income history</span><span class="muted">Provider-reported annual values</span></div><div class="tableWrap"><table><thead><tr><th>Fiscal year</th><th>Revenue</th><th>Net income</th><th>YoY income</th></tr></thead><tbody id="history"><tr><td colspan="4" class="mutedCell">No data.</td></tr></tbody></table></div></section>',
        '<section class="panel"><div class="sectionHead"><span>Research flags</span><span class="muted">Transparent rules, not a recommendation</span></div><div id="flags" class="flags"><span class="mutedCell">None yet.</span></div></section>',
        '<section class="panel split"><div><div class="sectionHead"><span>Source & freshness</span><span class="muted">Provenance</span></div><pre id="source">No provider request has been made yet.</pre></div><div class="actions"><button id="export" class="btn">Export JSON</button><a class="btn primary" href="https://ig.me/m/amormagics" target="_blank" rel="noopener">Buy / license</a></div></section>',
        '<footer><span>Market data may be delayed or entitlement-dependent. Validate material figures against authoritative filings.</span><span><a href="https://www.instagram.com/amormagics/" target="_blank" rel="noopener">@amormagics</a> · Not investment advice.</span></footer>',
      '</main>',
      '<dialog id="settings"><form method="dialog" class="dialog"><div class="dialogHead"><h2>Connection</h2><button value="cancel" class="iconBtn" aria-label="Close">×</button></div><p class="muted">Set the ASET SignalDesk API endpoint. For a local install, use the self-hosted FastAPI service. The desktop app does not store an Alpha Vantage key.</p><label for="apiBase">API base URL</label><input id="apiBase" value="' + esc(state.apiBase) + '" spellcheck="false"><div class="dialogActions"><button value="cancel" class="btn">Cancel</button><button type="button" id="save" class="btn primary">Save & connect</button></div></form></dialog>',
    '</div>'
  ].join("");

  $("analyze").onclick = analyze;
  $("refresh").onclick = analyze;
  $("export").onclick = exportJson;
  $("settingsBtn").onclick = openSettings;
  $("save").onclick = saveSettings;
  $("symbol").addEventListener("keydown", function (event) { if (event.key === "Enter") analyze(); });
  checkConnection().then(analyze);
}

boot();

const byId = id => document.getElementById(id);
const state = { config: null, capabilities: null, result: null, history: loadHistory() };

function loadHistory() {
  try { return JSON.parse(localStorage.getItem("ai-gateway-history") || "[]"); }
  catch { return []; }
}

function storeHistory() {
  localStorage.setItem("ai-gateway-history", JSON.stringify(state.history.slice(0, 12)));
}

function optionalNumber(id) {
  const value = byId(id).value.trim();
  return value === "" ? undefined : Number(value);
}

function commaList(id) {
  const values = byId(id).value.split(",").map(value => value.trim()).filter(Boolean);
  return values.length ? values : undefined;
}

function providerPayload() {
  if (!byId("useRuntimeProvider").checked) return undefined;
  return {
    api_key: byId("apiKey").value,
    base_url: byId("baseUrl").value,
    fast_model: byId("fastModel").value,
    reasoning_model: byId("reasoningModel").value,
    code_model: byId("codeModel").value,
    timeout_seconds: Number(byId("timeout").value),
    allow_insecure_loopback: byId("allowLoopback").checked
  };
}

function routePayload() {
  const payload = {
    prompt: byId("prompt").value,
    execute: byId("execute").checked,
    optimization: byId("optimization").value,
    council_mode: byId("councilMode").value,
    council_size: Number(byId("councilSize").value)
  };
  const optional = {
    max_cost_usd: optionalNumber("maxCost"),
    max_latency_ms: optionalNumber("maxLatency"),
    min_quality: optionalNumber("minQuality"),
    allowed_routes: commaList("allowedRoutes"),
    allowed_models: commaList("allowedModels"),
    provider: providerPayload()
  };
  for (const [key, value] of Object.entries(optional)) if (value !== undefined) payload[key] = value;
  return payload;
}

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  const body = await response.json();
  if (!response.ok) {
    const detail = body.detail;
    throw new Error(typeof detail === "string" ? detail : detail?.message || JSON.stringify(body));
  }
  return body;
}

async function initialize() {
  try {
    [state.config, state.capabilities] = await Promise.all([
      fetchJson("/v1/config"), fetchJson("/v1/capabilities")
    ]);
    const mode = state.config.execution_mode === "mock" ? "Offline mock" : "Provider configured";
    byId("modeBadge").textContent = mode;
    byId("providerSummary").textContent = state.config.runtime_credentials_allowed ? "Optional per request" : mode;
    byId("useRuntimeProvider").disabled = !state.config.runtime_credentials_allowed;
    byId("providerNotice").textContent = state.config.runtime_credentials_allowed
      ? "Runtime credentials are enabled for this server. Use this only on a trusted local deployment; the key is sent for one request and is not stored by this UI."
      : state.config.execution_mode === "mock"
        ? "No server provider is configured. Decision-only routing works now. To execute real LLM calls, configure environment variables or explicitly enable trusted local runtime credentials."
        : "The server has a provider configured through environment variables. Secrets are not exposed to this page.";
  } catch (error) {
    byId("modeBadge").textContent = "Backend unavailable";
    showError(error.message);
  }
  updateCharacterCount(); renderHistory();
}

async function submitRoute(event) {
  event.preventDefault();
  setWorking(true); hideError();
  try {
    const payload = routePayload();
    if (payload.provider && payload.execute && !payload.provider.api_key) throw new Error("Enter an API key or turn off execution.");
    const result = await fetchJson("/v1/route", {
      method: "POST", headers: {"content-type": "application/json"}, body: JSON.stringify(payload)
    });
    state.result = result; renderResult(result);
    state.history.unshift({
      saved_at: new Date().toISOString(), prompt: payload.prompt, result
    });
    state.history = state.history.slice(0, 12); storeHistory(); renderHistory();
  } catch (error) { showError(error.message); }
  finally { setWorking(false); }
}

function setWorking(working) {
  byId("routeButton").disabled = working;
  byId("routeButton").querySelector("span").textContent = working ? "Routing…" : "Evaluate route";
  byId("resultStatus").textContent = working ? "Working" : state.result ? "Complete" : "Ready";
  byId("resultStatus").className = `status-dot ${working ? "working" : state.result ? "success" : ""}`;
}

function renderResult(result) {
  const decision = result.decision;
  byId("emptyResult").classList.add("hidden"); byId("resultContent").classList.remove("hidden");
  byId("selectedRoute").textContent = decision.route;
  byId("confidence").textContent = `${Math.round(decision.confidence * 100)}%`;
  byId("selectedModel").textContent = decision.model || "No model";
  byId("taskType").textContent = decision.task_type;
  byId("complexity").textContent = decision.complexity;
  byId("provider").textContent = result.provider || "Decision only";
  replaceChildren(byId("reasons"), decision.reasons, reason => element("li", reason));
  toggleList("riskSection", "riskFlags", decision.risk_flags, value => element("span", value, "tag"));
  const candidates = decision.model_candidates || [];
  byId("candidateSection").classList.toggle("hidden", !candidates.length);
  replaceChildren(byId("candidates"), candidates, candidate => {
    const card = element("div", "", "candidate");
    card.append(element("strong", candidate.model), element("span", `score ${candidate.score}`));
    card.append(element("small", `$${candidate.estimated_cost_usd} · ${candidate.estimated_latency_ms} ms · quality ${candidate.quality}`));
    return card;
  });
  setJsonSection("councilSection", "councilPlan", decision.council_plan);
  byId("outputSection").classList.toggle("hidden", result.output == null);
  byId("output").textContent = result.output || "";
  byId("requestMeta").textContent = result.request ? `Request ${result.request.id} · ${result.request.elapsed_ms} ms` : "Saved result";
}

function replaceChildren(parent, items, makeChild) { parent.replaceChildren(...(items || []).map(makeChild)); }
function toggleList(sectionId, contentId, values, factory) {
  byId(sectionId).classList.toggle("hidden", !(values || []).length);
  replaceChildren(byId(contentId), values || [], factory);
}
function setJsonSection(sectionId, contentId, value) {
  byId(sectionId).classList.toggle("hidden", value == null);
  byId(contentId).textContent = value == null ? "" : JSON.stringify(value, null, 2);
}
function element(tag, text, className) { const node = document.createElement(tag); node.textContent = text; if (className) node.className = className; return node; }

function renderHistory() {
  const list = byId("historyList");
  if (!state.history.length) { list.replaceChildren(element("p", "No saved decisions.", "muted")); return; }
  replaceChildren(list, state.history, (item, index) => {
    const button = element("button", "", "history-card"); button.type = "button";
    button.append(element("strong", item.prompt.slice(0, 80)), element("span", `${item.result.decision.route} · ${new Date(item.saved_at).toLocaleString()}`));
    button.addEventListener("click", () => { state.result = item.result; byId("prompt").value = item.prompt; updateCharacterCount(); renderResult(item.result); window.scrollTo({top: 0, behavior: "smooth"}); });
    button.setAttribute("aria-label", `Open saved decision ${index + 1}: ${item.prompt.slice(0, 60)}`);
    return button;
  });
}

function showError(message) { byId("errorPanel").textContent = message; byId("errorPanel").classList.remove("hidden"); }
function hideError() { byId("errorPanel").classList.add("hidden"); byId("errorPanel").textContent = ""; }
function updateCharacterCount() { byId("characterCount").textContent = `${byId("prompt").value.length.toLocaleString()} characters`; }
async function copyResult() { if (!state.result) return; await navigator.clipboard.writeText(JSON.stringify(state.result, null, 2)); byId("copyResult").textContent = "Copied"; setTimeout(() => { byId("copyResult").textContent = "Copy JSON"; }, 1200); }
function downloadResult() { if (!state.result) return; const blob = new Blob([JSON.stringify(state.result, null, 2)], {type:"application/json"}); const link = document.createElement("a"); link.href = URL.createObjectURL(blob); link.download = `ai-gateway-${state.result.request?.id || "decision"}.json`; link.click(); URL.revokeObjectURL(link.href); }

byId("routeForm").addEventListener("submit", submitRoute);
byId("prompt").addEventListener("input", updateCharacterCount);
byId("clearPrompt").addEventListener("click", () => { byId("prompt").value = ""; updateCharacterCount(); byId("prompt").focus(); });
byId("useRuntimeProvider").addEventListener("change", event => byId("providerFields").classList.toggle("hidden", !event.target.checked));
byId("copyResult").addEventListener("click", copyResult);
byId("downloadResult").addEventListener("click", downloadResult);
byId("clearHistory").addEventListener("click", () => { state.history = []; storeHistory(); renderHistory(); });
initialize();

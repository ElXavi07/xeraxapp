const AGENT_URL = "http://127.0.0.1:47721";

const state = {
  token: sessionStorage.getItem("xeraxPairingToken") || "",
  device: null,
  uploadId: null,
};

const elements = {
  headerStatus: document.querySelector("#header-status"),
  connectionLabel: document.querySelector("#connection-label"),
  pairingPanel: document.querySelector("#pairing-panel"),
  devicePanel: document.querySelector("#device-panel"),
  tokenInput: document.querySelector("#pairing-token"),
  connectButton: document.querySelector("#connect-button"),
  scanButton: document.querySelector("#scan-button"),
  validateButton: document.querySelector("#validate-button"),
  rootButton: document.querySelector("#root-button"),
  imageInput: document.querySelector("#boot-image"),
  partition: document.querySelector("#partition"),
  profilePanel: document.querySelector("#profile-panel"),
  profileTitle: document.querySelector("#profile-title"),
  profileDetail: document.querySelector("#profile-detail"),
  confirmationPanel: document.querySelector("#confirmation-panel"),
  serialConfirmation: document.querySelector("#serial-confirmation"),
  backupConfirmation: document.querySelector("#backup-confirmation"),
  patchedConfirmation: document.querySelector("#patched-confirmation"),
  partitionConfirmation: document.querySelector("#partition-confirmation"),
  partitionConfirmationRow: document.querySelector("#partition-confirmation-row"),
  serialToType: document.querySelector("#serial-to-type"),
  log: document.querySelector("#live-log"),
  clearLog: document.querySelector("#clear-log"),
  deviceMode: document.querySelector("#device-mode"),
  deviceSerial: document.querySelector("#device-serial"),
  deviceModel: document.querySelector("#device-model"),
  deviceProduct: document.querySelector("#device-product"),
  deviceBuild: document.querySelector("#device-build"),
  deviceSlot: document.querySelector("#device-slot"),
  verifiedBootState: document.querySelector("#verified-boot-state"),
  unlockState: document.querySelector("#unlock-state"),
  profileState: document.querySelector("#profile-state"),
  adbStatus: document.querySelector("#adb-status"),
  fastbootStatus: document.querySelector("#fastboot-status"),
  releaseSummary: document.querySelector("#release-summary"),
  releaseVersion: document.querySelector("#release-version"),
  releaseHash: document.querySelector("#release-hash"),
  companionDownload: document.querySelector("#companion-download"),
  troubleshootingCode: document.querySelector("#troubleshooting-code"),
  troubleshootingText: document.querySelector("#troubleshooting-text"),
  diagnoseButton: document.querySelector("#diagnose-button"),
  diagnosticResults: document.querySelector("#diagnostic-results"),
};

function appendLog(message, level = "info") {
  const time = new Date().toLocaleTimeString([], { hour12: false });
  const prefix = level === "error" ? "error" : level === "ok" ? "ok" : "xerax";
  elements.log.textContent += `\n[${time}] [${prefix}] ${message}`;
  elements.log.scrollTop = elements.log.scrollHeight;
}

function renderPlatformTools(platformTools) {
  const adb = platformTools?.adb;
  const fastboot = platformTools?.fastboot;
  elements.adbStatus.textContent = adb?.available
    ? `adb: ${adb.version || "available"}`
    : "adb: missing";
  elements.fastbootStatus.textContent = fastboot?.available
    ? `fastboot: ${fastboot.version || "available"}`
    : "fastboot: missing";
  if (!platformTools?.ready) {
    appendLog("Android Platform Tools are incomplete. Use the official setup link.", "error");
  }
}

async function loadRelease() {
  try {
    const response = await fetch("./release.json", { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const release = await response.json();
    elements.releaseSummary.textContent =
      `${release.filename} for Windows. ${release.signed ? "Digitally signed." : "Preview build; not code-signed."}`;
    elements.releaseVersion.textContent = release.version;
    elements.releaseHash.textContent = release.sha256;
    elements.releaseHash.title = release.sha256;
    elements.companionDownload.href = release.url;
    elements.companionDownload.classList.remove("disabled-link");
    elements.companionDownload.removeAttribute("aria-disabled");
  } catch {
    elements.releaseSummary.textContent =
      "Release metadata is not available in this preview.";
  }
}

function setWorkflow(step) {
  document.querySelectorAll("[data-workflow-step]").forEach((item) => {
    item.classList.toggle("active", item.dataset.workflowStep === step);
  });
}

async function agentRequest(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (state.token) {
    headers.set("X-Xerax-Token", state.token);
  }

  const response = await fetch(`${AGENT_URL}${path}`, {
    ...options,
    headers,
  });

  let body;
  try {
    body = await response.json();
  } catch {
    body = { error: `Companion returned HTTP ${response.status}` };
  }

  if (!response.ok) {
    throw new Error(body.error || `Request failed with HTTP ${response.status}`);
  }

  return body;
}

function updateConnection(connected) {
  elements.headerStatus.classList.toggle("connected", connected);
  elements.consoleToolbar?.classList?.toggle("connected", connected);
  if (connected) {
    elements.headerStatus.lastChild.textContent = " Companion connected";
    elements.connectionLabel.textContent = "Companion connected";
    elements.pairingPanel.classList.add("hidden");
    elements.devicePanel.classList.remove("hidden");
  } else {
    elements.headerStatus.lastChild.textContent = " Companion offline";
    elements.connectionLabel.textContent = "Waiting for companion";
    elements.pairingPanel.classList.remove("hidden");
    elements.devicePanel.classList.add("hidden");
  }
}

function renderDevice(device) {
  state.device = device;
  elements.deviceMode.textContent = device.mode || "Not found";
  elements.deviceSerial.textContent = device.serial || "-";
  elements.deviceModel.textContent = device.model || "-";
  elements.deviceProduct.textContent = device.product || "-";
  elements.deviceBuild.textContent = device.ota_build || device.build_fingerprint || "-";
  elements.deviceSlot.textContent = device.current_slot || "-";
  elements.verifiedBootState.textContent = device.verified_boot_state || "-";
  elements.unlockState.textContent =
    device.unlocked === true ? "Verified unlocked" :
    device.unlocked === false ? "Locked" : "Unknown";
  elements.serialToType.textContent = device.serial || "";
  renderProfile(device.profile, device.profile_revision);

  if (device.mode === "fastboot" && device.unlocked === true) {
    appendLog(`Fastboot device ${device.serial} is verified unlocked.`, "ok");
    setWorkflow("image");
  } else if (device.mode === "adb") {
    appendLog("Device is in Android. Reboot it to the bootloader before flashing.");
    setWorkflow("inspect");
  } else {
    appendLog(device.message || "No supported device state detected.", "error");
    setWorkflow("inspect");
  }
}

function renderDiagnostics(diagnostics) {
  elements.diagnosticResults.replaceChildren();
  elements.diagnosticResults.classList.remove("hidden");
  if (!diagnostics.length) {
    const empty = document.createElement("p");
    empty.textContent =
      "No reviewed pattern matched. Keep the exact log and use device-specific documentation.";
    elements.diagnosticResults.append(empty);
    return;
  }

  diagnostics.forEach((diagnostic) => {
    const card = document.createElement("article");
    card.className = `diagnostic-card ${diagnostic.severity}`;

    const header = document.createElement("header");
    const title = document.createElement("strong");
    title.textContent = diagnostic.title;
    const scope = document.createElement("small");
    scope.textContent = `${diagnostic.severity} | ${diagnostic.scope}`;
    header.append(title, scope);

    const explanation = document.createElement("p");
    explanation.textContent = diagnostic.explanation;

    const actions = document.createElement("ol");
    diagnostic.actions.forEach((action) => {
      const item = document.createElement("li");
      item.textContent = action;
      actions.append(item);
    });

    const stops = document.createElement("ul");
    diagnostic.stop_conditions.forEach((condition) => {
      const item = document.createElement("li");
      item.textContent = `Stop: ${condition}`;
      stops.append(item);
    });

    card.append(header, explanation, actions, stops);
    elements.diagnosticResults.append(card);
  });
}

async function diagnoseProblem() {
  const code = elements.troubleshootingCode.value;
  const text = elements.troubleshootingText.value.trim();
  if (!code && !text) {
    appendLog("Choose a symptom or paste the exact error output.", "error");
    return;
  }
  try {
    const response = await agentRequest("/api/diagnose", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code, text }),
    });
    renderDiagnostics(response.diagnostics);
    appendLog(`Matched ${response.diagnostics.length} reviewed troubleshooting rule(s).`, "ok");
  } catch (error) {
    appendLog(error.message, "error");
  }
}

function renderProfile(profile, revision) {
  const matched = Boolean(profile);
  elements.profilePanel.classList.toggle("matched", matched);
  elements.partition.disabled = matched;
  elements.partitionConfirmationRow.classList.toggle("hidden", matched);
  elements.partitionConfirmation.checked = matched;

  if (matched) {
    elements.partition.value = profile.partition;
    elements.profileState.textContent = `${profile.status}: ${profile.profile_id}`;
    elements.profileTitle.textContent = `${profile.display_name} matched`;
    elements.profileDetail.textContent =
      `Manifest ${revision} requires ${profile.partition}. ${profile.notes || ""}`.trim();
    appendLog(
      `Exact ${profile.display_name} profile matched; target locked to ${profile.partition}.`,
      "ok",
    );
  } else {
    elements.profileState.textContent = `No match (${revision || "unknown manifest"})`;
    elements.profileTitle.textContent = "No exact device profile";
    elements.profileDetail.textContent =
      "Xerax will require you to verify the target partition from device-specific documentation.";
  }
}

async function scanDevice() {
  appendLog("Scanning ADB and fastboot transports...");
  setWorkflow("inspect");
  try {
    const result = await agentRequest("/api/device");
    renderDevice(result.device);
  } catch (error) {
    appendLog(error.message, "error");
  }
}

async function connect() {
  state.token = elements.tokenInput.value.trim();
  if (!/^\d{6}$/.test(state.token)) {
    appendLog("Enter the 6-digit pairing code shown by the companion.", "error");
    return;
  }

  try {
    const health = await agentRequest("/api/health");
    sessionStorage.setItem("xeraxPairingToken", state.token);
    updateConnection(true);
    appendLog(`Connected to Xerax companion ${health.version}.`, "ok");
    renderPlatformTools(health.platformTools);
    if (!health.flashingEnabled) {
      appendLog("Flashing is disabled. Restart companion with --enable-flashing to allow it.");
    }
    await scanDevice();
  } catch (error) {
    updateConnection(false);
    appendLog(error.message, "error");
  }
}

async function validateImage() {
  const file = elements.imageInput.files[0];
  if (!file) {
    appendLog("Choose a Magisk-patched .img file first.", "error");
    return;
  }

  if (!state.device || state.device.mode !== "fastboot" || state.device.unlocked !== true) {
    appendLog("A verified unlocked fastboot device is required.", "error");
    return;
  }

  appendLog(`Validating ${file.name} (${Math.round(file.size / 1024 / 1024)} MB)...`);
  try {
    const response = await agentRequest(
      `/api/image?filename=${encodeURIComponent(file.name)}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/octet-stream" },
        body: file,
      },
    );
    state.uploadId = response.uploadId;
    appendLog(response.message, "ok");
    elements.confirmationPanel.classList.remove("hidden");
    setWorkflow("confirm");
    updateRootButton();
  } catch (error) {
    state.uploadId = null;
    appendLog(error.message, "error");
  }
}

function updateRootButton() {
  const serialMatches =
    state.device && elements.serialConfirmation.value.trim() === state.device.serial;
  elements.rootButton.disabled = !(
    serialMatches &&
    elements.backupConfirmation.checked &&
    elements.patchedConfirmation.checked &&
    elements.partitionConfirmation.checked &&
    state.uploadId
  );
}

async function flashImage() {
  const payload = {
    uploadId: state.uploadId,
    serial: elements.serialConfirmation.value.trim(),
    partition: elements.partition.value,
    backupConfirmed: elements.backupConfirmation.checked,
    patchedConfirmed: elements.patchedConfirmation.checked,
    profileId: state.device?.profile?.profile_id || "",
  };

  elements.rootButton.disabled = true;
  appendLog(`Requesting flash to ${payload.partition}. Do not disconnect the device.`);
  try {
    const response = await agentRequest("/api/flash", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    response.log.forEach((line) => appendLog(line, "ok"));
    appendLog("Flash completed. The device reboot command was sent.", "ok");
  } catch (error) {
    appendLog(error.message, "error");
  } finally {
    updateRootButton();
  }
}

elements.connectButton.addEventListener("click", connect);
elements.scanButton.addEventListener("click", scanDevice);
elements.validateButton.addEventListener("click", validateImage);
elements.rootButton.addEventListener("click", flashImage);
elements.serialConfirmation.addEventListener("input", updateRootButton);
elements.backupConfirmation.addEventListener("change", updateRootButton);
elements.patchedConfirmation.addEventListener("change", updateRootButton);
elements.partitionConfirmation.addEventListener("change", updateRootButton);
elements.partition.addEventListener("change", updateRootButton);
elements.diagnoseButton.addEventListener("click", diagnoseProblem);
elements.clearLog.addEventListener("click", () => {
  elements.log.textContent = "[xerax] Log cleared.";
});
elements.tokenInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") connect();
});

if (state.token) {
  elements.tokenInput.value = state.token;
  connect();
}

loadRelease();

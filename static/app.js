const inputPath = document.querySelector("#inputPath");
const outputPath = document.querySelector("#outputPath");
const chooseInput = document.querySelector("#chooseInput");
const chooseOutput = document.querySelector("#chooseOutput");
const qualityMode = document.querySelector("#qualityMode");
const targetReduction = document.querySelector("#targetReduction");
const targetValue = document.querySelector("#targetValue");
const startButton = document.querySelector("#startButton");
const cancelButton = document.querySelector("#cancelButton");
const stage = document.querySelector("#stage");
const progressText = document.querySelector("#progressText");
const progressBar = document.querySelector("#progressBar");
const message = document.querySelector("#message");
const results = document.querySelector("#results");
const originalSize = document.querySelector("#originalSize");
const outputSize = document.querySelector("#outputSize");
const reduction = document.querySelector("#reduction");
const errorBox = document.querySelector("#errorBox");

let activeTaskId = null;
let pollTimer = null;

function setBusy(isBusy) {
  startButton.disabled = isBusy;
  cancelButton.disabled = !isBusy;
  chooseInput.disabled = isBusy;
  chooseOutput.disabled = isBusy;
}

function setProgress(value) {
  const clean = Math.max(0, Math.min(100, Number(value) || 0));
  progressBar.style.width = `${clean}%`;
  progressText.textContent = `${Math.round(clean)}%`;
}

async function postJson(url, body = {}) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Request failed");
  }
  return data;
}

function renderTask(task) {
  stage.textContent = task.stage || task.status;
  message.textContent = task.message || "";
  setProgress(task.progress);

  if (task.status === "done") {
    setBusy(false);
    clearInterval(pollTimer);
    results.hidden = false;
    originalSize.textContent = task.original_size_label;
    outputSize.textContent = task.output_size_label;
    reduction.textContent = task.reduction === null ? "-" : `${task.reduction}%`;
  }

  if (task.status === "error") {
    setBusy(false);
    clearInterval(pollTimer);
    errorBox.hidden = false;
    errorBox.textContent = task.error || "Compression failed.";
  }

  if (task.status === "cancelled") {
    setBusy(false);
    clearInterval(pollTimer);
    message.textContent = "Compression was cancelled.";
  }
}

async function pollProgress() {
  if (!activeTaskId) return;
  const response = await fetch(`/api/progress/${activeTaskId}`);
  const task = await response.json();
  renderTask(task);
}

chooseInput.addEventListener("click", async () => {
  const data = await postJson("/api/choose-input");
  if (data.path) inputPath.value = data.path;
});

chooseOutput.addEventListener("click", async () => {
  const data = await postJson("/api/choose-output", { input_path: inputPath.value });
  if (data.path) outputPath.value = data.path;
});

targetReduction.addEventListener("input", () => {
  targetValue.textContent = targetReduction.value;
});

startButton.addEventListener("click", async () => {
  errorBox.hidden = true;
  errorBox.textContent = "";
  results.hidden = true;
  setProgress(0);
  stage.textContent = "Starting";
  message.textContent = "Preparing compression job.";
  setBusy(true);

  try {
    const task = await postJson("/api/start", {
      input_path: inputPath.value,
      output_path: outputPath.value,
      quality_mode: qualityMode.value,
      target_reduction: targetReduction.value,
    });
    activeTaskId = task.id;
    renderTask(task);
    pollTimer = setInterval(pollProgress, 800);
  } catch (error) {
    setBusy(false);
    stage.textContent = "Ready";
    message.textContent = "Fix the issue and start again.";
    errorBox.hidden = false;
    errorBox.textContent = error.message;
  }
});

cancelButton.addEventListener("click", async () => {
  if (!activeTaskId) return;
  await postJson(`/api/cancel/${activeTaskId}`);
  message.textContent = "Cancelling after the current encoder step.";
});

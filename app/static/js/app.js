class CameraController {
  constructor(root) {
    this.root = root;
    this.video = root.querySelector("video");
    this.canvas = root.querySelector("canvas");
    this.stream = null;
  }

  async start() {
    if (this.stream) return;
    this.stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" }, audio: false });
    this.video.srcObject = this.stream;
  }

  captureDataUrl() {
    const context = this.canvas.getContext("2d");
    this.canvas.width = this.video.videoWidth || 640;
    this.canvas.height = this.video.videoHeight || 480;
    context.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
    return this.canvas.toDataURL("image/jpeg", 0.92);
  }
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    let detail = "Request failed.";
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch (_) {
      detail = response.statusText || detail;
    }
    throw new Error(detail);
  }
  return response.json();
}

function setText(el, html) {
  if (el) el.innerHTML = html;
}

function wireCameraCards() {
  const cards = document.querySelectorAll("[data-camera-root]");
  cards.forEach((root) => {
    const controller = new CameraController(root);
    const startButton = root.querySelector("[data-start-camera]");
    if (!startButton) return;
    startButton.addEventListener("click", async () => {
      try {
        await controller.start();
        const captureButton = root.querySelector("[data-capture-enrollment], [data-run-verification]");
        if (captureButton) captureButton.disabled = false;
        startButton.disabled = true;
        startButton.textContent = "Camera Ready";
      } catch (error) {
        alert(`Unable to start camera: ${error.message}`);
      }
    });
    root.cameraController = controller;
  });
}

function wireEnrollmentPage() {
  const form = document.querySelector("#enrollment-form");
  if (!form) return;
  const statusBox = document.querySelector("#enrollment-status");
  const captureButton = document.querySelector("[data-capture-enrollment]");
  const finalizeButton = document.querySelector("[data-finalize-enrollment]");
  const results = document.querySelector("#capture-results");
  const cameraRoot = document.querySelector("[data-camera-root]");
  const minCaptures = Number(form.dataset.minCaptures || "3");
  let sessionId = null;
  let acceptedCount = 0;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(form);
    const payload = {
      full_name: formData.get("full_name"),
      email: formData.get("email") || null,
      notes: formData.get("notes") || null,
      consent_given: formData.get("consent_given") === "on",
    };
    try {
      const response = await postJson("/api/enrollments/start", payload);
      sessionId = response.session_id;
      acceptedCount = response.accepted_count || 0;
      setText(statusBox, `<strong>Session ${sessionId} started.</strong><br>${response.message}`);
      captureButton.disabled = false;
    } catch (error) {
      setText(statusBox, `<strong>Unable to start enrollment.</strong><br>${error.message}`);
    }
  });

  captureButton?.addEventListener("click", async () => {
    if (!sessionId) {
      setText(statusBox, "<strong>Start enrollment first.</strong>");
      return;
    }
    try {
      const imageData = cameraRoot.cameraController.captureDataUrl();
      const response = await postJson(`/api/enrollments/${sessionId}/captures`, { image_data: imageData });
      acceptedCount = response.accepted_count;
      const item = document.createElement("li");
      item.innerHTML = `<strong>${response.message}</strong><br>Accepted captures: ${response.accepted_count} / ${minCaptures}<br>Reason codes: ${response.reason_codes.join(", ") || "none"}<br>Quality score: ${response.quality_score ?? "n/a"}`;
      results.prepend(item);
      finalizeButton.disabled = acceptedCount < minCaptures;
      setText(statusBox, `<strong>Capture ${response.capture_count} saved.</strong><br>Accepted captures: ${acceptedCount}.`);
    } catch (error) {
      setText(statusBox, `<strong>Capture failed.</strong><br>${error.message}`);
    }
  });

  finalizeButton?.addEventListener("click", async () => {
    try {
      const response = await postJson(`/api/enrollments/${sessionId}/finalize`, { session_id: sessionId });
      setText(statusBox, `<strong>${response.full_name} enrolled successfully.</strong><br>User ID: ${response.id}`);
      finalizeButton.disabled = true;
      captureButton.disabled = true;
    } catch (error) {
      setText(statusBox, `<strong>Unable to finalize enrollment.</strong><br>${error.message}`);
    }
  });
}

function wireVerificationPage() {
  const resultBox = document.querySelector("#verification-result");
  const verifyButton = document.querySelector("[data-run-verification]");
  const cameraRoot = document.querySelector("[data-camera-root]");
  const candidateField = document.querySelector("#candidate-user-id");
  if (!verifyButton || !resultBox || !cameraRoot) return;

  verifyButton.addEventListener("click", async () => {
    try {
      const imageData = cameraRoot.cameraController.captureDataUrl();
      const payload = { image_data: imageData, candidate_user_id: candidateField.value ? Number(candidateField.value) : null };
      const response = await postJson("/api/verifications", payload);
      const userLine = response.matched_user ? `Matched user: <strong>${response.matched_user.full_name}</strong><br>` : "";
      setText(
        resultBox,
        `<strong>Status: ${response.status}</strong><br>${userLine}Similarity score: ${response.similarity_score ?? "n/a"}<br>Threshold used: ${response.threshold_used}<br>Confidence: ${response.confidence_band}<br>Reason codes: ${response.reason_codes.join(", ")}`
      );
    } catch (error) {
      setText(resultBox, `<strong>Verification failed.</strong><br>${error.message}`);
    }
  });
}

function wireInlineDisableForms() {
  document.querySelectorAll("form[data-inline-post]").forEach((form) => {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const response = await fetch(form.action, { method: "POST" });
      if (response.ok) {
        window.location.reload();
      }
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  wireCameraCards();
  wireEnrollmentPage();
  wireVerificationPage();
  wireInlineDisableForms();
});


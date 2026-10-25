document.addEventListener("DOMContentLoaded", () => {
  // Theme Toggle
  const themeToggleBtn = document.getElementById("themeToggleBtn");
  themeToggleBtn.addEventListener("click", () => {
    document.body.classList.toggle("theme-light");
    document.body.classList.toggle("theme-dark");
  });

  // Tab Navigation
  const tabs = document.querySelectorAll(".nav-tab");
  const tabContents = document.querySelectorAll(".tab-content");

  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      tabContents.forEach(c => c.classList.remove("active"));

      tab.classList.add("active");
      const targetId = tab.getAttribute("data-tab");
      document.getElementById(targetId).classList.add("active");
    });
  });

  // Elements - Text Studio
  const intensitySlider = document.getElementById("intensitySlider");
  const intensityLabel = document.getElementById("intensityLabel");
  const inputText = document.getElementById("inputText");
  const outputText = document.getElementById("outputText");
  const humanizeBtn = document.getElementById("humanizeBtn");
  const loadSampleBtn = document.getElementById("loadSampleBtn");
  const clearBtn = document.getElementById("clearBtn");
  const copyBtn = document.getElementById("copyBtn");
  const inputWordCount = document.getElementById("inputWordCount");
  const outputWordCount = document.getElementById("outputWordCount");

  // Metrics
  const metricsBar = document.getElementById("metricsBar");
  const metricAiBefore = document.getElementById("metricAiBefore");
  const metricAiAfter = document.getElementById("metricAiAfter");
  const metricCliches = document.getElementById("metricCliches");
  const metricWatermarks = document.getElementById("metricWatermarks");
  const metricChanges = document.getElementById("metricChanges");

  // Intensity Slider Label
  intensitySlider.addEventListener("input", (e) => {
    const val = parseInt(e.target.value, 10);
    let desc = "Balanced";
    if (val < 40) desc = "Subtle";
    else if (val > 75) desc = "Aggressive";
    intensityLabel.textContent = `${desc} (${val}%)`;
  });

  function countWords(str) {
    if (!str.trim()) return 0;
    return str.trim().split(/\s+/).length;
  }

  inputText.addEventListener("input", () => {
    inputWordCount.textContent = `${countWords(inputText.value)} words`;
  });

  // Sample Thesis Text
  const SAMPLE_THESIS = `In conclusion, it is important to delve into the comprehensive tapestry of modern artificial intelligence methodologies. This study plays a pivotal role in illustrating that algorithmic frameworks stand as a testament to scientific innovation [1]. Furthermore, the interplay between stochastic optimization and computational scalability provides a robust framework for empirical inquiries. Moreover, in today's fast-paced digital era, the profound impact of automated systems cannot be overlooked [2]. The results indicate that the method converges rapidly. It requires fewer iterations than traditional heuristics. Future work should investigate these dynamics further.`;

  loadSampleBtn.addEventListener("click", () => {
    inputText.value = SAMPLE_THESIS;
    inputWordCount.textContent = `${countWords(inputText.value)} words`;
  });

  clearBtn.addEventListener("click", () => {
    inputText.value = "";
    outputText.value = "";
    inputWordCount.textContent = "0 words";
    outputWordCount.textContent = "0 words";
    metricsBar.style.display = "none";
  });

  // Humanize Action
  humanizeBtn.addEventListener("click", async () => {
    const text = inputText.value.trim();
    if (!text) {
      alert("Please paste thesis text to humanize.");
      return;
    }

    humanizeBtn.disabled = true;
    humanizeBtn.textContent = "⚡ Processing...";

    try {
      const intensity = parseInt(intensitySlider.value, 10) / 100.0;
      const res = await fetch("/api/humanize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, intensity })
      });
      const data = await res.json();

      outputText.value = data.cleaned_text;
      outputWordCount.textContent = `${countWords(data.cleaned_text)} words`;

      // Update metrics
      metricAiBefore.textContent = `${data.metrics_before.ai_risk}%`;
      metricAiAfter.textContent = `${data.metrics_after.ai_risk}%`;
      metricCliches.textContent = `${data.metrics_before.cliche_count} removed`;
      metricWatermarks.textContent = `${data.watermarks_found} Purged`;
      metricChanges.textContent = `${data.changes_count} sequences`;

      metricsBar.style.display = "grid";
    } catch (err) {
      alert("Error processing text: " + err);
    } finally {
      humanizeBtn.disabled = false;
      humanizeBtn.textContent = "⚡ Humanize Text";
    }
  });

  // Copy to Clipboard
  copyBtn.addEventListener("click", () => {
    if (!outputText.value.trim()) return;
    navigator.clipboard.writeText(outputText.value).then(() => {
      const orig = copyBtn.textContent;
      copyBtn.textContent = "✅ Copied!";
      setTimeout(() => { copyBtn.textContent = orig; }, 1800);
    });
  });

  // DOCX Drag & Drop Upload
  const dropArea = document.getElementById("dropArea");
  const docxFileInput = document.getElementById("docxFileInput");
  const selectedFileName = document.getElementById("selectedFileName");
  const processDocxBtn = document.getElementById("processDocxBtn");
  const docxUploadForm = document.getElementById("docxUploadForm");
  const docxIntensity = document.getElementById("docxIntensity");
  const docxStatus = document.getElementById("docxStatus");

  let currentDocxFile = null;

  dropArea.addEventListener("click", () => docxFileInput.click());

  dropArea.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropArea.classList.add("dragover");
  });

  dropArea.addEventListener("dragleave", () => {
    dropArea.classList.remove("dragover");
  });

  dropArea.addEventListener("drop", (e) => {
    e.preventDefault();
    dropArea.classList.remove("dragover");
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleDocxSelect(e.dataTransfer.files[0]);
    }
  });

  docxFileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleDocxSelect(e.target.files[0]);
    }
  });

  function handleDocxSelect(file) {
    if (!file.name.endsWith(".docx")) {
      alert("Please upload a .docx Microsoft Word file.");
      return;
    }
    currentDocxFile = file;
    selectedFileName.textContent = `Selected: ${file.name} (${Math.round(file.size / 1024)} KB)`;
    processDocxBtn.disabled = false;
  }

  docxUploadForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!currentDocxFile) return;

    processDocxBtn.disabled = true;
    processDocxBtn.textContent = "⏳ Humanizing Document in-place...";

    const formData = new FormData();
    formData.append("file", currentDocxFile);
    formData.append("intensity", docxIntensity.value);

    try {
      const res = await fetch("/api/upload-docx", {
        method: "POST",
        body: formData
      });

      if (!res.ok) throw new Error("Failed to process document");

      const blob = await res.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = downloadUrl;
      a.download = `Humanized_${currentDocxFile.name}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(downloadUrl);

      alert(`✅ Success! Humanized_${currentDocxFile.name} downloaded with all original formatting preserved.`);
    } catch (err) {
      alert("Error processing document: " + err.message);
    } finally {
      processDocxBtn.disabled = false;
      processDocxBtn.textContent = "⚡ Humanize Document & Download";
    }
  });

  // Zero-Width Scanner
  const scannerInput = document.getElementById("scannerInput");
  const scanBtn = document.getElementById("scanBtn");
  const scannerResult = document.getElementById("scannerResult");

  scanBtn.addEventListener("click", async () => {
    const text = scannerInput.value;
    if (!text.trim()) {
      alert("Please paste text to scan.");
      return;
    }

    const res = await fetch("/api/inspect-watermark", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text })
    });
    const data = await res.json();

    if (data.total_watermarks === 0) {
      scannerResult.innerHTML = `
        <h3 style="color: var(--success);">✅ Clean Text Detected</h3>
        <p>No invisible zero-width tracking characters or hidden watermarks were found.</p>
      `;
    } else {
      let list = "";
      for (const [charName, count] of Object.entries(data.details)) {
        list += `<li><strong>${charName}:</strong> ${count} found</li>`;
      }
      scannerResult.innerHTML = `
        <h3 style="color: var(--danger);">🚨 ${data.total_watermarks} Hidden Tracking Characters Found!</h3>
        <p>These hidden unicode characters trigger AI detectors and identify generated text:</p>
        <ul style="margin: 10px 0 10px 20px;">${list}</ul>
        <p><em>Use the Text Studio to purge them instantly.</em></p>
      `;
    }
    scannerResult.style.display = "block";
  });
});


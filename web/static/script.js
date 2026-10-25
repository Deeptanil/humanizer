document.addEventListener("DOMContentLoaded", () => {
  // Theme Toggle
  const themeToggleBtn = document.getElementById("themeToggleBtn");
  themeToggleBtn.addEventListener("click", () => {
    document.body.classList.toggle("theme-light");
    document.body.classList.toggle("theme-dark");
  });

  // Controls & Elements
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

  // SVGs for dynamic buttons
  const LIGHTNING_SVG = '<svg class="svg-icon" viewBox="0 0 24 24" width="16" height="16" fill="currentColor" stroke="currentColor" stroke-width="1.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>';
  const COPY_SVG = '<svg class="svg-icon" viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>';
  const CHECK_SVG = '<svg class="svg-icon" viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';

  // Intensity Slider Label
  intensitySlider.addEventListener("input", (e) => {
    const val = parseInt(e.target.value, 10);
    let desc = "Balanced";
    if (val < 40) desc = "Subtle";
    else if (val > 75) desc = "Aggressive";
    intensityLabel.textContent = `${desc} (${val}%)`;
  });

  function countWords(str) {
    if (!str || !str.trim()) return 0;
    return str.trim().split(/\s+/).length;
  }

  inputText.addEventListener("input", () => {
    inputWordCount.textContent = `${countWords(inputText.value)} words`;
  });

  // Realistic Thesis Sample (Zero Emojis)
  const SAMPLE_THESIS = `The rapid advancement of artificial intelligence has revolutionized many industries. However, there are still many challenges that need to be addressed. In this paper, we explore several solutions to improve the accuracy and efficiency of modern systems. Furthermore, our findings indicate that traditional methods are no longer sufficient [1]. Therefore, this study plays a pivotal role in illustrating the need for novel frameworks to foster a deeper understanding of computational scalability.`;

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
      alert("Please paste your thesis text to humanize.");
      return;
    }

    humanizeBtn.disabled = true;
    humanizeBtn.innerHTML = `${LIGHTNING_SVG} TRANSFORMING TEXT...`;

    try {
      const intensity = parseInt(intensitySlider.value, 10) / 100.0;
      const res = await fetch("/api/humanize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, intensity })
      });

      if (!res.ok) {
        throw new Error(`Server returned status ${res.status}`);
      }

      const data = await res.json();

      outputText.value = data.cleaned_text;
      outputWordCount.textContent = `${countWords(data.cleaned_text)} words`;

      // Update metrics HUD
      metricAiBefore.textContent = `${data.metrics_before.ai_risk}%`;
      metricAiAfter.textContent = `${data.metrics_after.ai_risk}%`;
      metricCliches.textContent = `${data.metrics_before.cliche_count} purged`;
      metricWatermarks.textContent = `${data.watermarks_found} purged`;
      metricChanges.textContent = `${data.changes_count} shifts`;

      metricsBar.style.display = "grid";
    } catch (err) {
      alert("Error processing text: " + err.message);
    } finally {
      humanizeBtn.disabled = false;
      humanizeBtn.innerHTML = `${LIGHTNING_SVG} HUMANIZE THESIS TEXT`;
    }
  });

  // Copy to Clipboard
  copyBtn.addEventListener("click", () => {
    if (!outputText.value.trim()) return;
    navigator.clipboard.writeText(outputText.value).then(() => {
      const origHtml = copyBtn.innerHTML;
      copyBtn.innerHTML = `${CHECK_SVG} COPIED!`;
      copyBtn.classList.remove("btn-accent");
      copyBtn.classList.add("btn-primary");
      setTimeout(() => {
        copyBtn.innerHTML = origHtml;
        copyBtn.classList.remove("btn-primary");
        copyBtn.classList.add("btn-accent");
      }, 1800);
    });
  });
});

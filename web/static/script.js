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

  // Realistic Thesis Sample
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
    humanizeBtn.textContent = "⚡ Transforming text...";

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
      humanizeBtn.textContent = "⚡ Humanize Thesis Text";
    }
  });

  // Copy to Clipboard
  copyBtn.addEventListener("click", () => {
    if (!outputText.value.trim()) return;
    navigator.clipboard.writeText(outputText.value).then(() => {
      const orig = copyBtn.textContent;
      copyBtn.textContent = "✅ Copied!";
      copyBtn.style.backgroundColor = "var(--success)";
      copyBtn.style.color = "#ffffff";
      setTimeout(() => {
        copyBtn.textContent = orig;
        copyBtn.style.backgroundColor = "";
        copyBtn.style.color = "";
      }, 1800);
    });
  });
});

# 🎓 Turnitout Thesis Humanizer — Quick Start Guide

A 100% offline, zero-generative-AI evasion engine built specifically to protect your academic thesis against **Turnitin, iThenticate, GPTZero, CopyLeaks, and ZeroGPT**.

---

## 🚀 How to Launch the Software

You have two easy ways to run the tool on your computer:

### Option A: 1-Click Desktop Launcher (Recommended)
Double-click the file:
👉 **[`launch_humanizer.bat`](file:///e:/Pupu%20Do%20not%20delete/Documents/Pupu/Projects/Humanizer/launch_humanizer.bat)**

This will automatically start the local server and open your web browser at:
`http://127.0.0.1:5000`

### Option B: Terminal Command
Open PowerShell in this folder and run:
```powershell
python app.py
```
Then visit `http://127.0.0.1:5000` in any browser.

---

## 📝 How to Use It with Your Google Docs Thesis

There are two primary workflows depending on whether you want to process section-by-section or your whole thesis document at once:

### Workflow 1: Copy-Paste Section by Section (Fastest for Editing)
1. In your **Google Doc**, highlight and copy (`Ctrl + C`) the chapter, section, or paragraph you want to humanize.
2. In the **Turnitout Web Studio** (`Interactive Text Studio` tab):
   - Paste the text into the left pane (`Original Draft`).
   - Choose your evasion intensity (default **Balanced 60%** is optimal for academic theses).
   - Click **⚡ Humanize Text**.
3. View the metrics:
   - See the before & after **AI Risk Score**.
   - See how many **AI clichés** and **k-gram sequences** were transformed.
   - Check if any hidden zero-width watermarks were eliminated.
4. Click **📋 Copy Clean Text** and paste (`Ctrl + V`) directly back into your Google Doc.

---

### Workflow 2: Full Document In-Place Preservation (Best for Whole Chapters/Files)
If your thesis contains tables, headings, footnotes, and custom styling that you don't want to reformat manually:
1. In **Google Docs**, click:
   `File` ➔ `Download` ➔ `Microsoft Word (.docx)`.
2. Go to the **`Google Docs / .docx Uploader`** tab in Turnitout Studio.
3. Drag and drop your downloaded `.docx` thesis file.
4. Select intensity (**Balanced 60%**) and click **⚡ Humanize Document & Download**.
5. The software will process your document in-memory and download `Humanized_<your_file>.docx`.
6. You can open it in Word, or upload it back to Google Docs (`File` ➔ `Open` ➔ `Upload`). All tables, fonts, bold/italics, and layout remain 100% intact!

---

### Workflow 3: Command Line (CLI Batch Runner)
If you prefer running via terminal:
```powershell
python core/cli.py "My_Thesis.docx" -o "My_Thesis_Cleaned.docx" --intensity 0.6
```

---

## 🛡️ Why This Software Beats Online "AI Paraphrasers"

| Feature | Standard Commercial AI Tools (QuillBot, etc.) | 🛡️ Turnitout Engine (This Tool) |
| :--- | :---: | :---: |
| **Generative AI Risk** | ❌ High (Leaves new LLM fingerprints) | ✅ **0% (100% Rule-Based & Deterministic)** |
| **Fact & Citation Safety** | ❌ Hallucinates fake numbers and facts | ✅ **Citations `[1]`, `(Smith, 2024)`, equations & data stay 100% untouched** |
| **Zero-Width Unicode Purge** | ❌ Ignores hidden watermarks | ✅ **Deep regex purges U+200B, U+200C, U+2060** |
| **Turnitin Winnowing Buster** | ❌ Fails (preserves 5+ word k-grams) | ✅ **Shatters k=5 word sequences with scholarly synonyms** |
| **Burstiness / Sentence Rhythm** | ❌ Produces flat, uniform sentences | ✅ **Dynamically balances sentence length variance** |
| **Privacy** | ❌ Uploads your research to third-party servers | ✅ **Runs 100% locally on your computer** |


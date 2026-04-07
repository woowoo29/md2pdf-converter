const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const fileRemove = document.getElementById('fileRemove');
const convertBtn = document.getElementById('convertBtn');
const convertForm = document.getElementById('convertForm');
const nextConvertBtn = document.getElementById('nextConvertBtn');
const errorBanner = document.getElementById('errorBanner');
const errorMsg = document.getElementById('errorMsg');

let selectedFile = null;
let desktopApi = null;
let isDesktopMode = false;
let pendingFileTimer = null;

// --- File selection ---
dropZone.addEventListener('click', async () => {
  if (isDesktopMode) {
    await openMarkdownFromDesktop();
    return;
  }

  fileInput.click();
});

fileInput.addEventListener('change', () => {
  if (fileInput.files[0]) setFile(fileInput.files[0]);
});

fileRemove.addEventListener('click', (e) => {
  e.stopPropagation();
  clearFile();
});

nextConvertBtn.addEventListener('click', () => {
  clearFile();
  dropZone.scrollIntoView({ behavior: 'smooth', block: 'center' });
});

// --- Drag and drop ---
dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
  dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  const file = e.dataTransfer.files[0];
  if (file) {
    if (!isSupportedMarkdownFilename(file.name)) {
      showError('.md 또는 .markdown 파일만 업로드할 수 있습니다.');
      return;
    }
    setFile(file);
  }
});

// --- Theme cards ---
document.querySelectorAll('.theme-card').forEach(card => {
  card.addEventListener('click', () => {
    document.querySelectorAll('.theme-card').forEach(c => c.classList.remove('active'));
    card.classList.add('active');
  });
});

// --- Form submit ---
convertForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  if (!selectedFile) return;

  hideError();
  setLoading(true);

  const formData = new FormData();
  formData.append('file', selectedFile);

  const activeTheme = document.querySelector('.theme-card.active');
  const theme = activeTheme ? activeTheme.dataset.theme : 'default';
  formData.append('theme', theme);

  try {
    if (isDesktopMode && desktopApi) {
      const conversion = await desktopApi.convert_markdown(
        selectedFile.name,
        await selectedFile.text(),
        theme,
      );
      if (!conversion || conversion.error) {
        throw new Error(conversion?.error || '앱 변환 중 오류가 발생했습니다.');
      }

      const saved = await desktopApi.save_pdf(conversion.filename, conversion.base64Pdf);
      if (saved && saved.error) {
        throw new Error(saved.error);
      }
      if (!saved || !saved.saved) {
        return;
      }
    } else {
      const response = await fetch('/convert', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || `서버 오류 (${response.status})`);
      }

      const blob = await response.blob();
      const disposition = response.headers.get('Content-Disposition');
      const filename = getDownloadFilename(disposition, selectedFile ? selectedFile.name : 'converted.pdf');
      downloadBlob(blob, filename);
    }

    nextConvertBtn.hidden = false;

  } catch (err) {
    showError(err.message || '변환 중 오류가 발생했습니다.');
  } finally {
    setLoading(false);
  }
});

// --- Helpers ---
function setFile(file) {
  selectedFile = file;
  fileName.textContent = file.name;
  dropZone.hidden = true;
  fileInfo.hidden = false;
  convertBtn.disabled = false;
  nextConvertBtn.hidden = true;
  hideError();
}

function clearFile() {
  selectedFile = null;
  fileInput.value = '';
  dropZone.hidden = false;
  fileInfo.hidden = true;
  convertBtn.disabled = true;
  nextConvertBtn.hidden = true;
  hideError();
}

function setLoading(loading) {
  const btnText = convertBtn.querySelector('.btn-text');
  const btnSpinner = convertBtn.querySelector('.btn-spinner');
  convertBtn.disabled = loading;
  btnText.hidden = loading;
  btnSpinner.hidden = !loading;
}

function showError(msg) {
  errorMsg.textContent = msg;
  errorBanner.hidden = false;
}

function hideError() {
  errorBanner.hidden = true;
}

function isSupportedMarkdownFilename(name) {
  return /\.(md|markdown)$/i.test(name);
}

async function openMarkdownFromDesktop() {
  if (!desktopApi) {
    return;
  }

  const payload = await desktopApi.open_markdown_dialog();
  await applyDesktopPayload(payload);
}

async function initializeDesktopMode() {
  desktopApi = await waitForDesktopApi();
  if (!desktopApi) {
    return;
  }

  isDesktopMode = true;
  const launchContext = await desktopApi.get_launch_context();
  if (launchContext && launchContext.openedFile) {
    await applyDesktopPayload(launchContext.openedFile);
  }

  window.addEventListener('desktop-open-file', () => {
    void checkPendingDesktopFile();
  });

  if (!pendingFileTimer) {
    pendingFileTimer = window.setInterval(checkPendingDesktopFile, 1000);
  }
}

async function waitForDesktopApi(timeoutMs = 4000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (window.pywebview && window.pywebview.api) {
      return window.pywebview.api;
    }
    await delay(50);
  }
  return null;
}

async function checkPendingDesktopFile() {
  if (!desktopApi) {
    return;
  }

  const payload = await desktopApi.consume_pending_open_file();
  if (payload) {
    await applyDesktopPayload(payload);
  }
}

async function applyDesktopPayload(payload) {
  if (!payload) {
    return;
  }

  if (payload.error) {
    showError(payload.error);
    return;
  }

  const file = new File([payload.content], payload.name, { type: 'text/markdown' });
  setFile(file);
}

function getDownloadFilename(disposition, selectedName) {
  if (disposition) {
    const utf8Match = disposition.match(/filename\*=UTF-8''([^;]+)/i);
    if (utf8Match) {
      return decodeURIComponent(utf8Match[1]);
    }

    const plainMatch = disposition.match(/filename="?([^"]+)"?/i);
    if (plainMatch) {
      return plainMatch[1];
    }
  }

  if (selectedName && isSupportedMarkdownFilename(selectedName)) {
    return selectedName.replace(/\.(md|markdown)$/i, '.pdf');
  }

  return 'converted.pdf';
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function delay(ms) {
  return new Promise(resolve => window.setTimeout(resolve, ms));
}

initializeDesktopMode();

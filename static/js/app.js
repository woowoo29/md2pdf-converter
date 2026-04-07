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

// --- File selection ---
dropZone.addEventListener('click', () => fileInput.click());

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
    if (!file.name.endsWith('.md')) {
      showError('.md 파일만 업로드할 수 있습니다.');
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
    const response = await fetch('/convert', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || `서버 오류 (${response.status})`);
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;

    const disposition = response.headers.get('Content-Disposition');
    const match = disposition && disposition.match(/filename="(.+)"/);
    a.download = match ? match[1] : 'converted.pdf';

    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
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

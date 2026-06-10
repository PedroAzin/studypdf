const uploadForm = document.querySelector("[data-upload-form]");
const uploadButton = document.querySelector("[data-upload-button]");
const uploadStatus = document.querySelector("[data-upload-status]");
const uploadStatusText = document.querySelector("[data-upload-status-text]");
const uploadProgress = document.querySelector("[data-upload-progress]");
const uploadDetail = document.querySelector("[data-upload-detail]");

function setUploadState({ text, detail, progress, indeterminate = false, error = false }) {
  uploadStatus.hidden = false;
  uploadStatus.classList.toggle("error", error);
  uploadStatus.classList.toggle("indeterminate", indeterminate);
  uploadStatusText.textContent = text;
  uploadDetail.textContent = detail || "";
  uploadProgress.value = progress;
}

function parseError(xhr) {
  try {
    const payload = JSON.parse(xhr.responseText);
    return payload.error || "Nao foi possivel enviar o PDF.";
  } catch (_error) {
    return "Nao foi possivel enviar o PDF.";
  }
}

if (uploadForm) {
  uploadForm.addEventListener("submit", (event) => {
    event.preventDefault();

    const fileInput = uploadForm.querySelector('input[type="file"]');
    if (!fileInput.files.length) {
      setUploadState({
        text: "Selecione um PDF",
        detail: "Escolha um arquivo antes de enviar.",
        progress: 0,
        error: true,
      });
      return;
    }

    const formData = new FormData(uploadForm);
    const xhr = new XMLHttpRequest();
    uploadButton.disabled = true;

    setUploadState({
      text: "Preparando envio",
      detail: fileInput.files[0].name,
      progress: 0,
    });

    xhr.upload.addEventListener("progress", (progressEvent) => {
      if (!progressEvent.lengthComputable) {
        setUploadState({
          text: "Enviando PDF",
          detail: "Aguardando progresso do navegador...",
          progress: 15,
          indeterminate: true,
        });
        return;
      }

      const percent = Math.round((progressEvent.loaded / progressEvent.total) * 100);
      setUploadState({
        text: `Enviando PDF (${percent}%)`,
        detail: "Depois do envio, o servidor extrai texto, imagens e sumario.",
        progress: Math.min(percent, 96),
      });
    });

    xhr.upload.addEventListener("load", () => {
      if (xhr.readyState !== XMLHttpRequest.DONE) {
        setUploadState({
          text: "Processando PDF",
          detail: "Extraindo paginas, imagens e capitulos. Isso pode levar alguns minutos.",
          progress: 98,
          indeterminate: true,
        });
      }
    });

    xhr.addEventListener("load", () => {
      uploadButton.disabled = false;
      if (xhr.status >= 200 && xhr.status < 300) {
        let redirectUrl = "";
        try {
          redirectUrl = JSON.parse(xhr.responseText).redirect_url;
        } catch (_error) {
          redirectUrl = xhr.responseURL;
        }

        setUploadState({
          text: "PDF enviado",
          detail: "Livro enviado para a fila de processamento. Abrindo a estante...",
          progress: 100,
        });
        window.location.href = redirectUrl || "/books";
        return;
      }

      setUploadState({
        text: "Falha no upload",
        detail: parseError(xhr),
        progress: 0,
        error: true,
      });
    });

    xhr.addEventListener("error", () => {
      uploadButton.disabled = false;
      setUploadState({
        text: "Erro de conexao",
        detail: "O servidor nao respondeu ao envio.",
        progress: 0,
        error: true,
      });
    });

    xhr.addEventListener("timeout", () => {
      uploadButton.disabled = false;
      setUploadState({
        text: "Tempo esgotado",
        detail: "O PDF pode ser grande demais ou o processamento demorou muito.",
        progress: 0,
        error: true,
      });
    });

    xhr.open("POST", uploadForm.action);
    xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");
    xhr.timeout = 10 * 60 * 1000;
    xhr.send(formData);
  });
}

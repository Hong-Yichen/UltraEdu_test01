(function () {
  const root = document.getElementById("tbp-reader-root");
  if (!root) return;
  const pdfUrl = root.dataset.pdfUrl;
  const TARGET_WIDTH = 800;

  const pdfCanvas = document.getElementById("tbp-pdf-canvas");
  const pageLabel = document.getElementById("tbp-page-label");
  const prevBtn = document.getElementById("tbp-prev-page");
  const nextBtn = document.getElementById("tbp-next-page");

  pdfjsLib.GlobalWorkerOptions.workerSrc =
    "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";

  let pdfDoc = null;
  let currentPage = 1;

  function renderPage(pageNumber) {
    currentPage = pageNumber;
    pageLabel.textContent = `Page ${pageNumber} / ${pdfDoc.numPages}`;
    prevBtn.disabled = pageNumber <= 1;
    nextBtn.disabled = pageNumber >= pdfDoc.numPages;

    pdfDoc.getPage(pageNumber).then((page) => {
      const naturalViewport = page.getViewport({ scale: 1 });
      const scale = TARGET_WIDTH / naturalViewport.width;
      const viewport = page.getViewport({ scale });
      pdfCanvas.width = viewport.width;
      pdfCanvas.height = viewport.height;
      const ctx = pdfCanvas.getContext("2d");
      page.render({ canvasContext: ctx, viewport: viewport });
    });
  }

  pdfjsLib.getDocument(pdfUrl).promise.then((pdf) => {
    pdfDoc = pdf;
    renderPage(1);
  });

  prevBtn.addEventListener("click", () => {
    if (currentPage > 1) renderPage(currentPage - 1);
  });
  nextBtn.addEventListener("click", () => {
    if (pdfDoc && currentPage < pdfDoc.numPages) renderPage(currentPage + 1);
  });
})();

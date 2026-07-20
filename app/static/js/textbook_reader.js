(function () {
  const root = document.getElementById("tb-reader-root");
  if (!root) return;
  const textbookId = root.dataset.textbookId;
  const pdfUrl = root.dataset.pdfUrl;
  const csrf = window.CSRF_TOKEN || "";
  const TARGET_WIDTH = 800;

  const pageContainer = document.getElementById("tb-page-container");
  const pdfCanvas = document.getElementById("tb-pdf-canvas");
  const annotationMount = document.getElementById("tb-annotation-mount");
  const pageLabel = document.getElementById("tb-page-label");
  const prevBtn = document.getElementById("tb-prev-page");
  const nextBtn = document.getElementById("tb-next-page");

  pdfjsLib.GlobalWorkerOptions.workerSrc =
    "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";

  let pdfDoc = null;
  let currentPage = 1;

  function getOrCreateCanvas(pageNumber, width, height) {
    return fetch(`/student/textbooks/${textbookId}/pages/${pageNumber}/canvas`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrf },
      body: JSON.stringify({ width: Math.round(width), height: Math.round(height) }),
    }).then((r) => r.json());
  }

  function renderPage(pageNumber) {
    currentPage = pageNumber;
    pageLabel.textContent = `Page ${pageNumber} / ${pdfDoc.numPages}`;
    prevBtn.disabled = pageNumber <= 1;
    nextBtn.disabled = pageNumber >= pdfDoc.numPages;

    annotationMount.innerHTML = "";
    const oldToolbar = pageContainer.querySelector(".uec-toolbar");
    if (oldToolbar) oldToolbar.remove();

    pdfDoc.getPage(pageNumber).then((page) => {
      const naturalViewport = page.getViewport({ scale: 1 });
      const provisionalScale = TARGET_WIDTH / naturalViewport.width;
      const provisionalWidth = naturalViewport.width * provisionalScale;
      const provisionalHeight = naturalViewport.height * provisionalScale;

      // The backend returns the EXISTING canvas size if this page already has one (e.g.
      // seeded ink), otherwise it creates one at our provisional size. Either way, we then
      // render the PDF at whatever scale reproduces that authoritative width exactly, so
      // the ink overlay always lines up pixel-for-pixel with the page underneath it.
      getOrCreateCanvas(pageNumber, provisionalWidth, provisionalHeight).then((data) => {
        const finalScale = data.width / naturalViewport.width;
        const viewport = page.getViewport({ scale: finalScale });
        pdfCanvas.width = viewport.width;
        pdfCanvas.height = viewport.height;
        const ctx = pdfCanvas.getContext("2d");
        page.render({ canvasContext: ctx, viewport: viewport }).promise.then(() => {
          UltraEduCanvas.mount(annotationMount, {
            documentId: data.document_id,
            mode: "edit",
            width: data.width,
            height: data.height,
          });
        });
      });
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

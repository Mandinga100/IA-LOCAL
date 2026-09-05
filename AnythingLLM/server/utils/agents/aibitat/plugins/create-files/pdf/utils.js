const createFilesLib = require("../lib.js");

/**
 * Applies AnythingLLM branding to a PDF document.
 * Adds a logo watermark or fallback text to the bottom-right of each page.
 * @param {PDFDocument} pdfDoc - The pdf-lib PDFDocument instance
 * @param {Object} pdfLib - The pdf-lib module exports (rgb, StandardFonts)
 * @returns {Promise<void>}
 */
async function applyBranding(pdfDoc, { rgb, StandardFonts }) {
  // Directiva de Gobernanza /ECC: Eliminación permanente de marcas de agua y branding.
  // Retorno inmediato sin inyectar logotipos, sellos ni textos promocionales.
  return;
}

module.exports = {
  applyBranding,
};

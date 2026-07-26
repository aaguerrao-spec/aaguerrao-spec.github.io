/* Process diagram engine — 100% frontend for GitHub Pages */
(function (global) {
  const STEP_PATTERNS = [
    /^\s*(?:paso|step|etapa|fase)\s*[\d]+[\s.\-:)]+\s*(.+)$/gim,
    /^\s*[\d]+[\s.\-:)]+(.+)$/gm,
    /^\s*[\-\*•>]\s+(.+)$/gm,
  ];

  const VERB_HINTS = /\b(registrar|validar|aprobar|revisar|enviar|recibir|clasificar|asignar|cerrar|iniciar|finalizar|verificar|analizar|procesar|notificar|escalar|documentar)\b/i;

  function normalizeLine(line) {
    return line.replace(/\s+/g, " ").trim();
  }

  function uniqueSteps(steps) {
    const seen = new Set();
    return steps.filter((step) => {
      const key = step.toLowerCase();
      if (seen.has(key) || step.length < 4) return false;
      seen.add(key);
      return true;
    });
  }

  function detectStepsFromText(text, filename) {
    const steps = [];
    const source = (text || "").replace(/\r/g, "\n");

    if (source.trim().length > 20) {
      for (const pattern of STEP_PATTERNS) {
        pattern.lastIndex = 0;
        let match;
        while ((match = pattern.exec(source)) !== null) {
          const step = normalizeLine(match[1] || match[0]);
          if (step.length >= 4 && step.length <= 120) steps.push(step);
        }
        if (steps.length >= 3) break;
      }

      if (steps.length < 3) {
        source.split("\n").forEach((line) => {
          const clean = normalizeLine(line);
          if (clean.length < 8 || clean.length > 120) return;
          if (VERB_HINTS.test(clean) || /^[A-ZÁÉÍÓÚ]/.test(clean)) {
            steps.push(clean.replace(/^[\-\d.\s)]+/, ""));
          }
        });
      }
    }

    const deduped = uniqueSteps(steps).slice(0, 12);
    if (deduped.length >= 2) return deduped;
    return detectStepsFromFilename(filename);
  }

  function detectStepsFromFilename(filename) {
    const name = (filename || "").toLowerCase();
    if (name.includes("onboarding") || name.includes("cliente")) {
      return ["Recepcion de solicitud", "Validacion inicial", "Revision documental", "Aprobacion", "Alta en sistema", "Seguimiento"];
    }
    if (name.includes("riesgo") || name.includes("risk")) {
      return ["Identificacion de riesgo", "Evaluacion", "Clasificacion", "Plan de tratamiento", "Monitoreo", "Cierre"];
    }
    if (name.includes("compra") || name.includes("proveedor")) {
      return ["Solicitud de compra", "Validacion presupuestal", "Cotizacion", "Aprobacion", "Orden de compra", "Recepcion"];
    }
    if (name.includes("incidente")) {
      return ["Registro", "Clasificacion", "Asignacion", "Tratamiento", "Validacion", "Cierre"];
    }
    return ["Ingreso del documento", "Interpretacion del flujo", "Validacion del proceso", "Definicion de responsables", "Control operativo", "Cierre del despliegue"];
  }

  async function readTextFile(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result || ""));
      reader.onerror = () => reject(new Error("No se pudo leer el archivo de texto."));
      reader.readAsText(file);
    });
  }

  async function readCsvFile(file) {
    const text = await readTextFile(file);
    return text.split("\n").slice(0, 50).join("\n");
  }

  async function readPdfFile(file) {
    if (!global.pdfjsLib) {
      throw new Error("PDF.js no cargado");
    }
    const data = new Uint8Array(await file.arrayBuffer());
    const pdf = await global.pdfjsLib.getDocument({ data }).promise;
    const pages = Math.min(pdf.numPages, 8);
    let text = "";
    for (let i = 1; i <= pages; i += 1) {
      const page = await pdf.getPage(i);
      const content = await page.getTextContent();
      const pageText = content.items.map((item) => item.str).join(" ");
      text += pageText + "\n";
    }
    return text.trim();
  }

  async function extractTextFromFile(file) {
    const ext = file.name.split(".").pop().toLowerCase();
    if (ext === "txt") return readTextFile(file);
    if (ext === "csv") return readCsvFile(file);
    if (ext === "pdf") return readPdfFile(file);
    throw new Error(`Formato .${ext} no soporta extraccion completa en frontend. Usa TXT o PDF.`);
  }

  global.ProcessEngine = {
    extractTextFromFile,
    detectStepsFromText,
    detectStepsFromFilename,
  };
})(window);

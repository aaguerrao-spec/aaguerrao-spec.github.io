/* Process diagram engine — 100% frontend for GitHub Pages */
(function (global) {
  const DURATION_RE = /^(\d+(?:[.,]\d+)?\s*(?:min(?:utos?)?|mins?|m|h(?:oras?)?|hr?s?|d(?:ías?|ias?)?|seg(?:undos?)?|s))$/i;
  const DURATION_INLINE = /(\d+(?:[.,]\d+)?\s*(?:min(?:utos?)?|mins?|m|h(?:oras?)?|hr?s?|d(?:ías?|ias?)?))/gi;
  const NUMBERED_RE = /^\s*(?:(?:paso|step|etapa|fase)\s*)?[\d]+(?:[.\-:)]\s*|\s*[\.\)]\s*)(.+)$/i;
  const BULLET_RE = /^\s*[\-\*•>]\s+(.+)$/;
  const TYPE_NO_VALOR = /no\s+valor\s+agregado/i;
  const TYPE_VALOR = /valor\s+agregado/i;
  const TYPE_CONTROL = /control\s+interno/i;
  const VERB_HINTS = /\b(registrar|validar|aprobar|revisar|enviar|recibir|clasificar|asignar|cerrar|iniciar|finalizar|verificar|analizar|procesar|notificar|escalar|documentar|recepci[oó]n|aprobaci[oó]n)\b/i;

  const TABLE_HEADERS = {
    name: /^(?:etapa|paso|actividad|proceso|nombre)/i,
    duration: /^(?:tiempo\s+de\s+ciclo|duraci[oó]n|cycle|tiempo\s+ciclo)/i,
    waitTime: /^(?:tiempo\s+de\s+espera|espera|wait|frecuencia)/i,
    responsible: /^(?:responsable|owner|area|[áa]rea)/i,
    type: /^(?:valor|tipo|clasificaci[oó]n|categor[ií]a)/i,
  };

  function normalizeLine(line) {
    return String(line || "").replace(/\s+/g, " ").trim();
  }

  function emptyStep(name) {
    return {
      name: name || "",
      duration: null,
      waitTime: null,
      responsible: null,
      type: "unknown",
      typeLabel: null,
    };
  }

  function classifyType(text) {
    const value = normalizeLine(text);
    if (!value) return { type: "unknown", typeLabel: null };
    if (TYPE_NO_VALOR.test(value)) return { type: "no-valor", typeLabel: "No valor agregado" };
    if (TYPE_VALOR.test(value)) return { type: "valor", typeLabel: "Valor agregado" };
    if (TYPE_CONTROL.test(value)) return { type: "control", typeLabel: "Control interno" };
    return { type: "unknown", typeLabel: value };
  }

  function isDurationLine(line) {
    return DURATION_RE.test(normalizeLine(line));
  }

  function isTypeLine(line) {
    const clean = normalizeLine(line);
    return TYPE_NO_VALOR.test(clean) || TYPE_VALOR.test(clean);
  }

  function isResponsibleHint(line) {
    const clean = normalizeLine(line);
    if (!clean || isDurationLine(clean) || isTypeLine(clean)) return false;
    if (TYPE_CONTROL.test(clean)) return true;
    return /^(operaciones|gerencia|administraci[oó]n|control interno|log[ií]stica|compras|finanzas|ti|rrhh)$/i.test(clean);
  }

  function stepIsComplete(step) {
    return Boolean(step.name && (step.duration || step.waitTime || step.responsible || step.typeLabel));
  }

  function finalizeStep(step) {
    const result = { ...step };
    if (!result.name) return null;
    if (result.type === "unknown" && result.typeLabel) {
      const classified = classifyType(result.typeLabel);
      if (classified.type !== "unknown") {
        result.type = classified.type;
        result.typeLabel = classified.typeLabel;
      }
    }
    if (result.responsible && TYPE_CONTROL.test(result.responsible) && result.type === "unknown") {
      result.type = "control";
      result.typeLabel = "Control interno";
    }
    return result;
  }

  function parseInlineRow(line) {
    const parts = line.split(/\s*[|;,]\s*|\t+/).map(normalizeLine).filter(Boolean);
    if (parts.length < 3) return null;
    const step = emptyStep(parts[0]);
    parts.slice(1).forEach((part) => {
      if (isDurationLine(part)) {
        if (!step.duration) step.duration = part;
        else if (!step.waitTime) step.waitTime = part;
      } else if (isTypeLine(part)) {
        Object.assign(step, classifyType(part));
      } else if (isResponsibleHint(part) || !step.responsible) {
        if (isResponsibleHint(part) || (!step.duration && !step.waitTime)) {
          step.responsible = part;
        }
      }
    });
    return step.name ? finalizeStep(step) : null;
  }

  function parseTableRows(lines) {
    const rows = [];
    let columnMap = null;

    for (const rawLine of lines) {
      const line = normalizeLine(rawLine.replace(/^\|/, "").replace(/\|$/, ""));
      if (!line || /^[-:\s|]+$/.test(line)) continue;

      const cells = line.includes("|")
        ? line.split("|").map(normalizeLine).filter(Boolean)
        : line.includes("\t")
          ? line.split("\t").map(normalizeLine).filter(Boolean)
          : null;

      if (!cells || cells.length < 3) continue;

      const headerLike = cells.some((cell) =>
        Object.values(TABLE_HEADERS).some((re) => re.test(cell))
      );

      if (headerLike && !columnMap) {
        columnMap = {};
        cells.forEach((cell, index) => {
          Object.entries(TABLE_HEADERS).forEach(([key, re]) => {
            if (re.test(cell)) columnMap[key] = index;
          });
        });
        continue;
      }

      if (columnMap && Object.keys(columnMap).length >= 2) {
        const step = emptyStep(cells[columnMap.name ?? 0]);
        if (columnMap.duration != null) step.duration = cells[columnMap.duration] || null;
        if (columnMap.waitTime != null) step.waitTime = cells[columnMap.waitTime] || null;
        if (columnMap.responsible != null) step.responsible = cells[columnMap.responsible] || null;
        if (columnMap.type != null) Object.assign(step, classifyType(cells[columnMap.type] || ""));
        const finalized = finalizeStep(step);
        if (finalized) rows.push(finalized);
        continue;
      }

      if (cells.length >= 4 && !cells[0].match(/^(?:etapa|paso)/i)) {
        const step = emptyStep(cells[0]);
        step.duration = cells[1] || null;
        step.waitTime = cells[2] || null;
        step.responsible = cells[3] || null;
        if (cells[4]) Object.assign(step, classifyType(cells[4]));
        const finalized = finalizeStep(step);
        if (finalized) rows.push(finalized);
      }
    }

    return rows.length >= 2 ? rows : [];
  }

  function parseBlockSteps(lines) {
    const steps = [];
    let current = null;

    function pushCurrent() {
      if (!current) return;
      const finalized = finalizeStep(current);
      if (finalized && finalized.name) steps.push(finalized);
      current = null;
    }

    for (const rawLine of lines) {
      const line = normalizeLine(rawLine);
      if (!line) continue;

      const inline = parseInlineRow(line);
      if (inline) {
        pushCurrent();
        steps.push(inline);
        continue;
      }

      const numbered = !isDurationLine(line) ? line.match(NUMBERED_RE) : null;
      const bullet = line.match(BULLET_RE);
      const startsNew =
        numbered ||
        bullet ||
        (current && stepIsComplete(current) && !isDurationLine(line) && !isTypeLine(line) && !isResponsibleHint(line));

      if (startsNew) {
        pushCurrent();
        current = emptyStep((numbered && numbered[1]) || (bullet && bullet[1]) || line);
        continue;
      }

      if (!current) {
        current = emptyStep(line);
        continue;
      }

      if (isTypeLine(line)) {
        Object.assign(current, classifyType(line));
      } else if (isDurationLine(line)) {
        if (!current.duration) current.duration = line;
        else if (!current.waitTime) current.waitTime = line;
        else pushCurrent(), (current = emptyStep(line));
      } else if (isResponsibleHint(line) || !current.responsible) {
        current.responsible = line;
      } else if (!current.typeLabel && classifyType(line).type !== "unknown") {
        Object.assign(current, classifyType(line));
      } else {
        pushCurrent();
        current = emptyStep(line);
      }
    }

    pushCurrent();
    return steps;
  }

  function parseSimpleSteps(lines) {
    const steps = [];
    for (const rawLine of lines) {
      const line = normalizeLine(rawLine);
      if (!line) continue;
      const numbered = !isDurationLine(line) ? line.match(NUMBERED_RE) : null;
      const bullet = line.match(BULLET_RE);
      if (numbered) {
        steps.push(finalizeStep(emptyStep(numbered[1])));
        continue;
      }
      if (bullet) {
        steps.push(finalizeStep(emptyStep(bullet[1])));
        continue;
      }
      if (line.length >= 4 && line.length <= 120 && (VERB_HINTS.test(line) || /^[A-ZÁÉÍÓÚÑ]/.test(line))) {
        steps.push(finalizeStep(emptyStep(line.replace(/^[\-\d.\s)]+/, ""))));
      }
    }
    return steps.filter(Boolean);
  }

  function uniqueSteps(steps) {
    const seen = new Set();
    return steps.filter((step) => {
      const key = (step.name || "").toLowerCase();
      if (!key || key.length < 3 || seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }

  function parseProcessSteps(text, filename) {
    const source = (text || "").replace(/\r/g, "\n");
    const lines = source.split("\n").map(normalizeLine);

    if (source.trim().length > 20) {
      const tableSteps = parseTableRows(lines);
      if (tableSteps.length >= 2) return uniqueSteps(tableSteps).slice(0, 16);

      const blockSteps = parseBlockSteps(lines);
      if (blockSteps.length >= 2) return uniqueSteps(blockSteps).slice(0, 16);

      const simpleSteps = parseSimpleSteps(lines);
      if (simpleSteps.length >= 2) return uniqueSteps(simpleSteps).slice(0, 16);
    }

    return detectStepsFromFilename(filename);
  }

  function detectStepsFromText(text, filename) {
    return parseProcessSteps(text, filename);
  }

  function detectStepsFromFilename(filename) {
    const name = (filename || "").toLowerCase();
    if (name.includes("compra") || name.includes("proveedor") || name.includes("flujo") || name.includes("vsm")) {
      return [
        { name: "Recepcion", duration: "15 min", waitTime: "10 min", responsible: "Operaciones", type: "valor", typeLabel: "Valor agregado" },
        { name: "Validacion", duration: "30 min", waitTime: "4 h", responsible: "Control interno", type: "no-valor", typeLabel: "No valor agregado" },
        { name: "Aprobacion", duration: "20 min", waitTime: "2 h", responsible: "Gerencia", type: "valor", typeLabel: "Valor agregado" },
        { name: "Registro", duration: "12 min", waitTime: "35 min", responsible: "Administracion", type: "valor", typeLabel: "Valor agregado" },
      ];
    }
    if (name.includes("incidente")) {
      return [
        { name: "Registro", duration: "10 min", waitTime: "5 min", responsible: "Operaciones", type: "valor", typeLabel: "Valor agregado" },
        { name: "Clasificacion", duration: "20 min", waitTime: "1 h", responsible: "Control interno", type: "no-valor", typeLabel: "No valor agregado" },
        { name: "Tratamiento", duration: "45 min", waitTime: "2 h", responsible: "Operaciones", type: "valor", typeLabel: "Valor agregado" },
        { name: "Cierre", duration: "15 min", waitTime: "30 min", responsible: "Control interno", type: "control", typeLabel: "Control interno" },
      ];
    }
    return [
      { name: "Ingreso del documento", duration: "5 min", waitTime: null, responsible: null, type: "valor", typeLabel: "Valor agregado" },
      { name: "Interpretacion del flujo", duration: "15 min", waitTime: "10 min", responsible: "Operaciones", type: "valor", typeLabel: "Valor agregado" },
      { name: "Validacion del proceso", duration: "30 min", waitTime: "4 h", responsible: "Control interno", type: "no-valor", typeLabel: "No valor agregado" },
      { name: "Cierre del despliegue", duration: "10 min", waitTime: null, responsible: "Administracion", type: "valor", typeLabel: "Valor agregado" },
    ];
  }

  function normalizeStep(step) {
    if (typeof step === "string") return finalizeStep(emptyStep(step));
    return finalizeStep({ ...emptyStep(step.name), ...step });
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
    return text.split("\n").slice(0, 80).join("\n");
  }

  async function readPdfFile(file) {
    if (!global.pdfjsLib) throw new Error("PDF.js no cargado");
    const data = new Uint8Array(await file.arrayBuffer());
    const pdf = await global.pdfjsLib.getDocument({ data }).promise;
    const pages = Math.min(pdf.numPages, 8);
    let text = "";
    for (let i = 1; i <= pages; i += 1) {
      const page = await pdf.getPage(i);
      const content = await page.getTextContent();
      text += content.items.map((item) => item.str).join(" ") + "\n";
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
    parseProcessSteps,
    detectStepsFromText,
    detectStepsFromFilename,
    normalizeStep,
  };
})(window);

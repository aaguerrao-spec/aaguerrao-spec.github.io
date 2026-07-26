/* Procedure generator — 100% frontend for GitHub Pages */
(function (global) {
  const STEP_LINE = /^\s*(?:[\d]+[\s.\-:)]\s*|[\-*•>]\s*)(.+)$/;

  function normalize(text) {
    return String(text || "").replace(/\s+/g, " ").trim();
  }

  function parseStepsText(text, defaultResponsible) {
    const lines = String(text || "")
      .replace(/\r/g, "\n")
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean);

    const steps = [];
    for (const line of lines) {
      const match = line.match(STEP_LINE);
      const raw = match ? match[1] : line;
      const parts = raw.split(/\s*[|;,]\s*/).map(normalize).filter(Boolean);
      const descripcion = parts[0] || raw;
      if (descripcion.length < 2) continue;
      steps.push({
        descripcion,
        responsable: parts[1] || defaultResponsible || null,
        entrada: parts[2] || null,
        salida: parts[3] || null,
      });
    }
    return steps;
  }

  function buildProcedure(fields) {
    const responsable = normalize(fields.responsable);
    return {
      nombre: normalize(fields.nombre),
      responsable: responsable || null,
      objetivo: normalize(fields.objetivo),
      alcance: normalize(fields.alcance),
      entradas: normalize(fields.entradas),
      salidas: normalize(fields.salidas),
      pasos: parseStepsText(fields.pasos, responsable),
    };
  }

  function validateProcedure(proc) {
    const errors = [];
    if (!proc.nombre) errors.push("El nombre del procedimiento es obligatorio.");
    if (!proc.objetivo) errors.push("El objetivo es obligatorio.");
    if (!proc.pasos.length) errors.push("Debes indicar al menos un paso en la lista de actividades.");
    return errors;
  }

  function formatList(value) {
    if (!value) return "No especificado.";
    return value
      .split(/[,;\n]/)
      .map((item) => normalize(item))
      .filter(Boolean)
      .map((item) => `• ${item}`)
      .join("\n");
  }

  function formatDocumentText(proc) {
    const pasosText = proc.pasos
      .map((step, index) => {
        const extras = [
          step.responsable ? `Responsable: ${step.responsable}` : null,
          step.entrada ? `Entrada: ${step.entrada}` : null,
          step.salida ? `Salida: ${step.salida}` : null,
        ]
          .filter(Boolean)
          .join(" | ");
        return `${index + 1}. ${step.descripcion}${extras ? `\n   ${extras}` : ""}`;
      })
      .join("\n");

    return [
      `PROCEDIMIENTO: ${proc.nombre}`,
      "",
      "1. OBJETIVO",
      proc.objetivo,
      "",
      "2. ALCANCE",
      proc.alcance || "No especificado.",
      "",
      "3. RESPONSABLE",
      proc.responsable || "No especificado.",
      "",
      "4. ENTRADAS",
      formatList(proc.entradas),
      "",
      "5. SALIDAS",
      formatList(proc.salidas),
      "",
      "6. DESARROLLO DEL PROCEDIMIENTO",
      pasosText,
      "",
      "7. CONTROL Y SEGUIMIENTO",
      "Toda ejecucion debera quedar registrada, validada y trazable para revision posterior.",
      "",
      "8. CRITERIO DE CIERRE",
      "El procedimiento se considera cerrado una vez se verifique la evidencia, se registre el resultado y se notifique a las partes interesadas.",
    ].join("\n");
  }

  function buildFlowNodes(proc) {
    const nodes = [{ type: "start", label: "Inicio" }];
    proc.pasos.forEach((step, index) => {
      nodes.push({
        type: "step",
        label: step.descripcion,
        index: index + 1,
        responsable: step.responsable,
      });
    });
    nodes.push({ type: "end", label: "Fin" });
    return nodes;
  }

  global.ProcedureEngine = {
    buildProcedure,
    validateProcedure,
    parseStepsText,
    formatDocumentText,
    buildFlowNodes,
  };
})(window);

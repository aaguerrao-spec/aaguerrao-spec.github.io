/* Value Stream Mapping engine — 100% frontend for GitHub Pages */
(function (global) {
  const DURATION_RE = /(\d+(?:[.,]\d+)?)\s*(min(?:utos?)?|mins?|m|h(?:oras?)?|hr?s?|d(?:ías?|ias?)?|seg(?:undos?)?|s)?/i;
  const TYPE_NO_VALOR = /no\s+valor\s+agregado/i;
  const TYPE_VALOR = /valor\s+agregado/i;

  const DEFAULT_STAGES = [
    { etapa: "Recepcion", ciclo: "15 min", espera: "10 min", responsable: "Operaciones", valor: "valor" },
    { etapa: "Validacion", ciclo: "30 min", espera: "4 h", responsable: "Control interno", valor: "no-valor" },
    { etapa: "Aprobacion", ciclo: "20 min", espera: "2 h", responsable: "Gerencia", valor: "valor" },
    { etapa: "Registro", ciclo: "12 min", espera: "35 min", responsable: "Administracion", valor: "valor" },
  ];

  function normalize(text) {
    return String(text || "").replace(/\s+/g, " ").trim();
  }

  function parseDurationToMinutes(text) {
    const value = normalize(text).toLowerCase();
    if (!value) return 0;
    const match = value.match(DURATION_RE);
    if (!match) return 0;
    const amount = parseFloat(match[1].replace(",", "."));
    const unit = (match[2] || "min").toLowerCase();
    if (unit.startsWith("h")) return amount * 60;
    if (unit.startsWith("d")) return amount * 24 * 60;
    if (unit.startsWith("s") && !unit.startsWith("seg")) return amount / 60;
    if (unit === "m" && !unit.startsWith("min")) return amount;
    return amount;
  }

  function formatMinutes(totalMin) {
    if (!totalMin || totalMin <= 0) return "0 min";
    if (totalMin >= 60) {
      const hours = Math.floor(totalMin / 60);
      const mins = Math.round(totalMin % 60);
      return mins ? `${hours} h ${mins} min` : `${hours} h`;
    }
    return `${Math.round(totalMin)} min`;
  }

  function classifyValor(text) {
    const value = normalize(text);
    if (TYPE_NO_VALOR.test(value)) return "no-valor";
    if (TYPE_VALOR.test(value)) return "valor";
    return value.toLowerCase().includes("no") ? "no-valor" : "valor";
  }

  function normalizeStage(raw) {
    const valor = classifyValor(raw.valor);
    const cicloMin = parseDurationToMinutes(raw.ciclo);
    const esperaMin = parseDurationToMinutes(raw.espera);
    return {
      etapa: normalize(raw.etapa),
      ciclo: normalize(raw.ciclo),
      espera: normalize(raw.espera),
      responsable: normalize(raw.responsable),
      valor,
      valorLabel: valor === "no-valor" ? "No valor agregado" : "Valor agregado",
      cicloMin,
      esperaMin,
      totalMin: cicloMin + esperaMin,
    };
  }

  function parseStages(rows) {
    return rows
      .map(normalizeStage)
      .filter((stage) => stage.etapa.length > 0);
  }

  function validateStages(stages) {
    const errors = [];
    if (!stages.length) errors.push("Agrega al menos una etapa al mapa de flujo de valor.");
    stages.forEach((stage, index) => {
      if (!stage.cicloMin && !stage.esperaMin) {
        errors.push(`La etapa "${stage.etapa}" (fila ${index + 1}) no tiene tiempos validos.`);
      }
    });
    return errors;
  }

  function calculateMetrics(stages) {
    let totalCycle = 0;
    let totalWait = 0;
    let valueAdded = 0;
    let nonValueAdded = 0;

    stages.forEach((stage) => {
      totalCycle += stage.cicloMin;
      totalWait += stage.esperaMin;
      if (stage.valor === "valor") {
        valueAdded += stage.cicloMin;
        nonValueAdded += stage.esperaMin;
      } else {
        nonValueAdded += stage.cicloMin + stage.esperaMin;
      }
    });

    const leadTime = totalCycle + totalWait;
    const valueAddedPct = leadTime > 0 ? (valueAdded / leadTime) * 100 : 0;

    return {
      totalCycle,
      totalWait,
      leadTime,
      valueAdded,
      nonValueAdded,
      valueAddedPct,
      totalCycleLabel: formatMinutes(totalCycle),
      totalWaitLabel: formatMinutes(totalWait),
      leadTimeLabel: formatMinutes(leadTime),
      valueAddedLabel: formatMinutes(valueAdded),
      nonValueAddedLabel: formatMinutes(nonValueAdded),
      valueAddedPctLabel: `${valueAddedPct.toFixed(1)}%`,
    };
  }

  function detectBottleneck(stages) {
    if (!stages.length) return null;

    let maxWait = stages[0];
    let maxCycle = stages[0];
    let maxTotal = stages[0];

    stages.forEach((stage) => {
      if (stage.esperaMin > maxWait.esperaMin) maxWait = stage;
      if (stage.cicloMin > maxCycle.cicloMin) maxCycle = stage;
      if (stage.totalMin > maxTotal.totalMin) maxTotal = stage;
    });

    const reason =
      maxTotal === maxWait && maxWait.esperaMin >= maxWait.cicloMin
        ? "mayor tiempo de espera"
        : maxTotal === maxCycle
          ? "mayor tiempo de ciclo"
          : "mayor tiempo combinado";

    return {
      stage: maxTotal,
      maxWaitStage: maxWait,
      maxCycleStage: maxCycle,
      reason,
      label: `${maxTotal.etapa} (${reason}: ${formatMinutes(maxTotal.totalMin)})`,
    };
  }

  global.VsmEngine = {
    DEFAULT_STAGES,
    parseDurationToMinutes,
    formatMinutes,
    classifyValor,
    parseStages,
    validateStages,
    calculateMetrics,
    detectBottleneck,
  };
})(window);

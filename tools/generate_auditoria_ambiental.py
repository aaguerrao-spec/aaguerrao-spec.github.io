#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generador de planilla Excel - Auditoría Técnico-Ambiental Mensual Río Ventisquero."""

import os
import sys
from copy import copy

from openpyxl import Workbook
from openpyxl.chart import BarChart, PieChart, Reference
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.table import Table, TableStyleInfo

sys.path.insert(0, os.path.dirname(__file__))
from audit_data import (  # noqa: E402
    COMUNA,
    CONTRATO,
    DOCUMENTOS_BASE,
    EMPRESA,
    INSTALACION,
    LISTAS,
    MANDANTE,
    MESES_AUDITORIA,
    PLAN_MANEJO,
    REGION,
    REQUISITOS,
    TEMAS_CAPACITACION,
    VERSION_ARCHIVO,
)

OUTPUT = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "Auditoria_Tecnico_Ambiental_Mensual_Instalacion_Rio_Ventisquero.xlsx",
)

# Colores corporativos
C_AZUL = "1F4E79"
C_VERDE = "2E7D32"
C_GRIS = "F2F2F2"
C_AMARILLO = "FFF2CC"
C_ROJO = "FFCCCC"
C_ROJO_OSC = "C00000"
C_NARANJA = "FCE4D6"
C_AZUL_CL = "DDEBF7"
C_VERDE_CL = "E2EFDA"
C_HEADER = "D9E1F2"
C_TITLE = "1F3864"

THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
FONT_TITLE = Font(name="Calibri", size=16, bold=True, color=C_TITLE)
FONT_HDR = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
FONT_BODY = Font(name="Calibri", size=10)
FILL_HDR = PatternFill("solid", fgColor=C_AZUL)
FILL_TITLE = PatternFill("solid", fgColor=C_GRIS)


def style_header_row(ws, row, ncols):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = FONT_HDR
        cell.fill = FILL_HDR
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER


def auto_width(ws, min_w=8, max_w=45):
    for col in ws.columns:
        letter = get_column_letter(col[0].column)
        length = max(len(str(c.value or "")) for c in col)
        ws.column_dimensions[letter].width = min(max(length + 2, min_w), max_w)


def add_table(ws, name, ref):
    tab = Table(displayName=name, ref=ref)
    tab.tableStyleInfo = TableStyleInfo(
        name="TableStyleMedium2",
        showFirstColumn=False,
        showLastColumn=False,
        showRowStripes=True,
        showColumnStripes=False,
    )
    ws.add_table(tab)


def list_range(sheet_name, col, n):
    col_l = get_column_letter(col)
    return f"'{sheet_name}'!${col_l}$2:${col_l}${n + 1}"


def build_listas(wb):
    ws = wb.create_sheet("_Listas", 0)
    ws.sheet_state = "hidden"
    col = 1
    named = {}
    for key, items in LISTAS.items():
        ws.cell(1, col, key.replace("_", " ").title())
        for i, v in enumerate(items, 2):
            ws.cell(i, col, v)
        named[key] = (col, len(items))
        col += 1
    ws.cell(1, col, "Mes auditoría")
    for i, m in enumerate(MESES_AUDITORIA, 2):
        ws.cell(i, col, m)
    named["mes_auditoria"] = (col, len(MESES_AUDITORIA))
    col += 1
    ws.cell(1, col, "Temas capacitación")
    for i, t in enumerate(TEMAS_CAPACITACION, 2):
        ws.cell(i, col, t)
    named["temas_cap"] = (col, len(TEMAS_CAPACITACION))
    return ws, named


def dv_list(formula, allow_blank=True):
    d = DataValidation(type="list", formula1=formula, allow_blank=allow_blank)
    d.error = "Seleccione un valor de la lista"
    d.errorTitle = "Valor no válido"
    return d


def build_portada(wb):
    ws = wb.create_sheet("Portada")
    ws.merge_cells("A1:H1")
    ws["A1"] = "AUDITORÍA TÉCNICO-AMBIENTAL MENSUAL"
    ws["A1"].font = FONT_TITLE
    ws["A1"].alignment = Alignment(horizontal="center")

    ws.merge_cells("A2:H2")
    ws["A2"] = PLAN_MANEJO
    ws["A2"].font = Font(size=11, bold=True)
    ws["A2"].alignment = Alignment(horizontal="center", wrap_text=True)

    ws["A4"] = "Espacio logotipos mandante / ejecutora"
    ws.merge_cells("A4:D8")
    ws["A4"].fill = FILL_TITLE
    ws["A4"].alignment = Alignment(horizontal="center", vertical="center")

    fields = [
        ("Contrato:", CONTRATO),
        ("Instalación de faenas:", INSTALACION),
        ("Empresa ejecutora:", EMPRESA),
        ("Mandante:", MANDANTE),
        ("Región:", REGION),
        ("Comuna:", COMUNA),
        ("Duración contractual:", "720 días (mayo 2026 – mayo 2028)"),
        ("Periodo auditado:", ""),
        ("Mes y año de auditoría:", ""),
        ("Nombre del auditor:", ""),
        ("Cargo:", ""),
        ("Fecha de elaboración:", ""),
        ("Fecha de revisión:", ""),
        ("Fecha de aprobación:", ""),
        ("Estado general de la auditoría:", ""),
        ("Versión del archivo:", VERSION_ARCHIVO),
    ]
    r = 10
    for label, val in fields:
        ws.cell(r, 1, label).font = Font(bold=True)
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=6)
        c = ws.cell(r, 2, val)
        c.border = BORDER
        c.alignment = Alignment(wrap_text=True)
        r += 1

    ws.merge_cells(f"A{r + 1}:H{r + 4}")
    adv = ws.cell(
        r + 1,
        1,
        "ADVERTENCIA: Esta planilla constituye una herramienta de control y seguimiento. "
        "No reemplaza la revisión profesional de la normativa vigente, permisos, resoluciones, "
        "bases contractuales ni instrucciones de la Inspección Fiscal.",
    )
    adv.alignment = Alignment(wrap_text=True, vertical="top")
    adv.font = Font(italic=True, color="7F6000")
    adv.fill = PatternFill("solid", fgColor=C_AMARILLO)

    ws["H10"] = "Mes auditado (lista):"
    ws["H11"] = "=Config!B3"
    auto_width(ws)
    ws.column_dimensions["A"].width = 28
    ws.column_dimensions["B"].width = 70
    return ws


def build_config(wb, listas_named):
    ws = wb.create_sheet("Config")
    ws["A1"] = "Parámetros de la auditoría mensual"
    ws["A1"].font = Font(bold=True, size=12)
    ws["A2"] = "Mes y año auditado"
    ws["B2"] = "05-2026"
    col, n = listas_named["mes_auditoria"]
    dv = dv_list(list_range("_Listas", col, n))
    ws.add_data_validation(dv)
    dv.add(ws["B2"])
    ws["A3"] = "Referencia mes (celda vinculada)"
    ws["B3"] = "=B2"
    ws["A4"] = "Fecha referencia (último día mes)"
    ws["B4"] = '=FIN.MES(FECHA(VALOR(DERECHA(B2;4));VALOR(IZQUIERDA(B2;2));1);0)'
    ws["A5"] = "Nombre auditor"
    ws["B5"] = ""
    ws["A6"] = "Cargo auditor"
    ws["B6"] = "Encargado ambiental"
    ws["A8"] = "Ponderación estados (editable)"
    ws["A9"], ws["B9"] = "Cumple", 1
    ws["A10"], ws["B10"] = "Cumple parcialmente", 0.5
    ws["A11"], ws["B11"] = "No cumple", 0
    ws["A12"], ws["B12"] = "En proceso de regularización", 0.25
    auto_width(ws)
    return ws


def build_instrucciones(wb):
    ws = wb.create_sheet("Instrucciones")
    lines = [
        "INSTRUCTIVO DE USO — AUDITORÍA TÉCNICO-AMBIENTAL MENSUAL",
        "",
        "1. CÓMO COMPLETAR LA PLANILLA",
        "   a) En la hoja Config, seleccione el mes y año auditado.",
        "   b) Revise el Catálogo de requisitos (referencia base del PMA Rev. 1).",
        "   c) Complete la Matriz de auditoría mensual verificando cada requisito.",
        "   d) Registre hallazgos en la hoja correspondiente y vincule el ID de requisito.",
        "   e) Actualice permisos, residuos, agua/sanitarios, capacitaciones y registro fotográfico.",
        "   f) Revise el Dashboard e Informe mensual automático antes de emitir el informe al mandante.",
        "",
        "2. ESTADOS DE CUMPLIMIENTO",
        "   • Cumple: evidencia objetiva demuestra cumplimiento total.",
        "   • Cumple parcialmente: cumplimiento incompleto o con deficiencias menores.",
        "   • No cumple: incumplimiento verificado.",
        "   • No aplica: requisito no aplicable al periodo o instalación.",
        "   • Pendiente de verificación: aún no verificado en el mes.",
        "   • En proceso de regularización: acción correctiva en curso.",
        "",
        "3. CLASIFICACIÓN DE HALLAZGOS",
        "   • Crítico: riesgo ambiental alto o incumplimiento grave.",
        "   • Mayor: incumplimiento significativo con plazo de corrección.",
        "   • Menor: desviación de bajo impacto.",
        "   • Observación: mejora recomendada sin incumplimiento formal.",
        "   • Buena práctica: desempeño destacado.",
        "",
        "4. REGISTRO DE EVIDENCIAS",
        "   Describa la evidencia revisada, indique tipo, código documental y enlace digital o ruta de archivo.",
        "",
        "5. GESTIÓN DE HALLAZGOS",
        "   Todo incumplimiento relevante debe registrarse en 'Registro de hallazgos' con responsable y fechas.",
        "",
        "6. FILTROS E INDICADORES",
        "   Use filtros de tablas Excel. El Dashboard se actualiza automáticamente desde la Matriz y otras hojas.",
        "",
        "7. HISTORIAL MENSUAL",
        "   Duplique el archivo al cierre de cada mes (Archivo > Guardar como) conservando el mes auditado.",
        "",
        "INSTRUCTIVO EN 5 PASOS:",
        "   Paso 1: Configurar mes auditado en hoja Config.",
        "   Paso 2: Verificar requisitos en Matriz de auditoría mensual.",
        "   Paso 3: Registrar hallazgos, documentos y evidencias.",
        "   Paso 4: Revisar Dashboard e indicadores.",
        "   Paso 5: Copiar resumen de Informe mensual al informe al mandante / IF.",
    ]
    for i, line in enumerate(lines, 1):
        ws.cell(i, 1, line)
        if line.startswith("INSTRUCTIVO") or line.startswith("INSTRUCTIVO EN"):
            ws.cell(i, 1).font = Font(bold=True, size=12)
        elif line and line[0].isdigit():
            ws.cell(i, 1).font = Font(bold=True)
    ws.column_dimensions["A"].width = 110
    return ws


def build_catalogo(wb, listas_named):
    ws = wb.create_sheet("Catálogo de requisitos")
    headers = [
        "ID", "Componente ambiental", "Subcomponente", "Etapa", "Área/ubicación",
        "Requisito auditable", "Medida/obligación/compromiso", "Fuente documental",
        "Norma/permiso/referencia", "Frecuencia", "Indicador/criterio", "Método verificación",
        "Resultado esperado", "Tipo obligación", "Nivel certeza requisito", "Ponderación default",
    ]
    ws.append(headers)
    style_header_row(ws, 1, len(headers))
    for req in REQUISITOS:
        ws.append(list(req))
    last = len(REQUISITOS) + 1
    add_table(ws, "TablaCatalogo", f"A1:{get_column_letter(len(headers))}{last}")
    ws.freeze_panes = "A2"
    auto_width(ws)
    return ws, last


def build_matriz(wb, listas_named, n_req):
    ws = wb.create_sheet("Matriz auditoría mensual")
    headers = [
        "ID requisito", "Componente ambiental", "Subcomponente", "Etapa proyecto",
        "Área/ubicación", "Requisito auditable", "Medida/obligación/compromiso",
        "Fuente documental", "Norma/permiso/referencia", "Frecuencia control",
        "Indicador/criterio verificación", "Método verificación", "Resultado esperado",
        "Estado cumplimiento", "Nivel hallazgo", "Descripción evidencia revisada",
        "Tipo evidencia", "Documento respaldo", "Enlace evidencia", "Fecha verificación",
        "Responsable verificación", "Responsable acción correctiva", "Fecha comprometida cierre",
        "Fecha real cierre", "Días atraso", "Acción correctiva/preventiva", "Estado hallazgo",
        "Observaciones auditor", "Comunicar IF", "Folio comunicación/informe",
        "Foto antes", "Foto después", "Validación responsable", "Ponderación",
        "% cumplimiento fila", "Tipo obligación", "Nivel certeza requisito",
    ]
    ws.append(headers)
    style_header_row(ws, 1, len(headers))

    # Copiar catálogo base + columnas de auditoría vacías
    for req in REQUISITOS:
        base = list(req[:13])  # hasta resultado esperado
        row_data = base + [""] * 20 + [req[15], "", req[13], req[14]]
        ws.append(row_data)

    first_data, last_data = 2, n_req + 1

    # Validaciones
    lmap = listas_named
    validations = [
        (14, "estado_cumplimiento"), (15, "nivel_hallazgo"), (17, "tipo_evidencia"),
        (21, "responsables"), (22, "responsables"), (27, "estado_hallazgo"), (29, "si_no"),
    ]
    for col_idx, key in validations:
        col, n = lmap[key]
        dv = dv_list(list_range("_Listas", col, n))
        ws.add_data_validation(dv)
        dv.add(f"{get_column_letter(col_idx)}{first_data}:{get_column_letter(col_idx)}{last_data + 50}")

    # Fórmulas por fila
    for r in range(first_data, last_data + 1):
        ws.cell(r, 25, f'=SI(Y(W{r}<>"";X{r}="");HOY()-W{r};SI(Y(W{r}<>"";X{r}<>"");X{r}-W{r};""))')
        ws.cell(r, 34, f'=SI(N{r}="Cumple";Config!$B$9;SI(N{r}="Cumple parcialmente";Config!$B$10;SI(N{r}="No cumple";Config!$B$11;SI(N{r}="En proceso de regularización";Config!$B$12;SI(N{r}="No aplica";"NA";"PEND")))))')
        ws.cell(r, 35, f'=SI(AH{r}="NA";"NA";SI(AH{r}="PEND";"PEND";AH{r}*100))')
        for dc in (20, 23, 24):
            ws.cell(r, dc).number_format = "DD-MM-YYYY"

    # Formato condicional semáforo columna N
    ws.conditional_formatting.add(
        f"N{first_data}:N{last_data + 50}",
        CellIsRule(operator="equal", formula=['"Cumple"'], fill=PatternFill("solid", fgColor=C_VERDE_CL)),
    )
    ws.conditional_formatting.add(
        f"N{first_data}:N{last_data + 50}",
        CellIsRule(operator="equal", formula=['"Cumple parcialmente"'], fill=PatternFill("solid", fgColor=C_AMARILLO)),
    )
    ws.conditional_formatting.add(
        f"N{first_data}:N{last_data + 50}",
        CellIsRule(operator="equal", formula=['"No cumple"'], fill=PatternFill("solid", fgColor=C_ROJO)),
    )
    ws.conditional_formatting.add(
        f"N{first_data}:N{last_data + 50}",
        CellIsRule(operator="equal", formula=['"Pendiente de verificación"'], fill=PatternFill("solid", fgColor="E7E6E6")),
    )

    add_table(ws, "TablaMatriz", f"A1:{get_column_letter(len(headers))}{last_data}")
    ws.freeze_panes = "A2"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToPage = True
    ws.page_setup.fitToWidth = 1
    ws.print_title_rows = "1:1"
    auto_width(ws)
    return ws, last_data


def build_hallazgos(wb, listas_named):
    ws = wb.create_sheet("Registro hallazgos")
    headers = [
        "ID hallazgo", "Fecha detección", "Mes auditoría", "ID requisito", "Componente ambiental",
        "Descripción hallazgo", "Evidencia objetiva", "Nivel hallazgo", "Riesgo ambiental",
        "Requisito incumplido", "Acción inmediata", "Acción correctiva definitiva", "Responsable",
        "Fecha comprometida", "Fecha cierre", "Estado", "Días abiertos", "Días atraso",
        "Verificación eficacia", "Responsable verificar cierre", "Evidencia cierre",
        "Comunicar mandante", "Folio comunicación", "Observaciones",
    ]
    ws.append(headers)
    style_header_row(ws, 1, len(headers))
    for i in range(2, 52):
        ws.cell(i, 1, f"HAL-{i-1:03d}")
        ws.cell(i, 3, "=Config!B2")
        ws.cell(i, 17, f'=SI(Y(B{i}<>"";O{i}="");HOY()-B{i};SI(Y(B{i}<>"";O{i}<>"");O{i}-B{i};""))')
        ws.cell(i, 18, f'=SI(Y(N{i}<>"";O{i}="");HOY()-N{i};SI(Y(N{i}<>"";O{i}<>"");O{i}-N{i};""))')
        ws.cell(i, 2).number_format = "DD-MM-YYYY"
        ws.cell(i, 14).number_format = "DD-MM-YYYY"
        ws.cell(i, 15).number_format = "DD-MM-YYYY"

    lmap = listas_named
    for col_idx, key in [(8, "nivel_hallazgo"), (9, "riesgo_ambiental"), (16, "estado_hallazgo"),
                         (13, "responsables"), (20, "responsables"), (22, "si_no")]:
        col, n = lmap[key]
        dv = dv_list(list_range("_Listas", col, n))
        ws.add_data_validation(dv)
        dv.add(f"{get_column_letter(col_idx)}2:{get_column_letter(col_idx)}100")

    # Formato condicional hallazgos
    rules = [
        ('$H2="Crítico"', PatternFill("solid", fgColor=C_ROJO_OSC), Font(color="FFFFFF")),
        ('$H2="Mayor"', PatternFill("solid", fgColor=C_ROJO), None),
        ('$H2="Menor"', PatternFill("solid", fgColor=C_AMARILLO), None),
        ('$H2="Observación"', PatternFill("solid", fgColor=C_AZUL_CL), None),
        ('$H2="Buena práctica"', PatternFill("solid", fgColor=C_VERDE_CL), None),
    ]
    rng = "A2:X100"
    for formula, fill, font in rules:
        ws.conditional_formatting.add(rng, FormulaRule(formula=[formula], fill=fill, font=font))
    ws.conditional_formatting.add(
        "A2:X100",
        FormulaRule(
            formula=['Y($N2<>"";$O2="";$N2<HOY())'],
            fill=PatternFill("solid", fgColor=C_ROJO_OSC),
            font=Font(color="FFFFFF"),
        ),
    )
    ws.conditional_formatting.add(
        "A2:X100",
        FormulaRule(
            formula=['Y($N2<>"";$O2="";$N2-HOY()<=7;$N2>=HOY())'],
            fill=PatternFill("solid", fgColor=C_NARANJA),
        ),
    )

    add_table(ws, "TablaHallazgos", f"A1:{get_column_letter(len(headers))}51")
    ws.freeze_panes = "A2"
    auto_width(ws)
    return ws


def build_documentos(wb, listas_named):
    ws = wb.create_sheet("Control permisos")
    headers = [
        "ID documental", "Tipo documento", "Documento/permiso", "Materia", "Autoridad emisora",
        "Titular", "N° resolución/certificado", "Fecha emisión", "Fecha vencimiento", "Vigencia (días rest.)",
        "Estado documental (auto)", "Responsable", "Ubicación archivo", "Enlace digital",
        "Fecha última revisión", "Observaciones",
    ]
    ws.append(headers)
    style_header_row(ws, 1, len(headers))
    for doc in DOCUMENTOS_BASE:
        ws.append(list(doc) + ["", "", ""])
    first, last = 2, len(DOCUMENTOS_BASE) + 1
    for r in range(first, last + 20):
        ws.cell(r, 10, f'=SI(I{r}="";"";I{r}-HOY())')
        ws.cell(
            r,
            11,
            f'=SI(I{r}="";"No disponible";SI(J{r}<0;"Vencido";SI(J{r}<=30;"Por vencer en 30 días";SI(J{r}<=60;"Por vencer en 60 días";"Vigente"))))',
        )
        ws.cell(r, 8).number_format = "DD-MM-YYYY"
        ws.cell(r, 9).number_format = "DD-MM-YYYY"
    add_table(ws, "TablaDocumentos", f"A1:{get_column_letter(len(headers))}{last + 20}")
    ws.freeze_panes = "A2"
    # CF documentos
    ws.conditional_formatting.add(
        f"K{first}:K{last + 20}",
        CellIsRule(operator="equal", formula=['"Vencido"'], fill=PatternFill("solid", fgColor=C_ROJO)),
    )
    ws.conditional_formatting.add(
        f"K{first}:K{last + 20}",
        CellIsRule(operator="equal", formula=['"Por vencer en 30 días"'], fill=PatternFill("solid", fgColor=C_NARANJA)),
    )
    auto_width(ws)
    return ws


def build_residuos(wb, listas_named):
    ws = wb.create_sheet("Registro residuos")
    headers = [
        "Mes", "Fecha", "Área generadora", "Tipo residuo", "Clasificación", "Peligrosidad",
        "Código/descripción", "Cantidad", "Unidad", "Contenedor", "Fecha retiro", "Transportista",
        "Autorización transportista", "Destino final", "Autorización destino",
        "N° guía/manifiesto/certificado", "Evidencia", "Observaciones",
    ]
    ws.append(headers)
    style_header_row(ws, 1, len(headers))
    ws.cell(2, 1, "=Config!B2")
    lmap = listas_named
    for col_idx, key in [(4, "tipo_residuo"), (9, "unidad")]:
        col, n = lmap[key]
        dv = dv_list(list_range("_Listas", col, n))
        ws.add_data_validation(dv)
        dv.add(f"{get_column_letter(col_idx)}2:{get_column_letter(col_idx)}200")
    add_table(ws, "TablaResiduos", f"A1:{get_column_letter(len(headers))}200")
    ws.freeze_panes = "A2"
    auto_width(ws)
    return ws


def build_agua(wb):
    ws = wb.create_sheet("Agua y sanitarios")
    headers = [
        "Mes", "Fecha", "Tipo control", "Sistema/instalación", "Agua potable", "Cloro residual",
        "Resultado análisis", "Limpieza fosa séptica", "Limpieza baño químico",
        "Limpieza cámara desgrasadora", "Empresa prestadora", "N° resolución sanitaria",
        "Certificado/respaldo", "Resultado", "Observaciones",
    ]
    ws.append(headers)
    style_header_row(ws, 1, len(headers))
    ws.cell(2, 1, "=Config!B2")
    add_table(ws, "TablaAgua", f"A1:{get_column_letter(len(headers))}200")
    ws.freeze_panes = "A2"
    auto_width(ws)
    return ws


def build_capacitaciones(wb, listas_named):
    ws = wb.create_sheet("Capacitaciones")
    headers = [
        "Fecha", "Tema", "Tipo capacitación", "Relator", "Cargo", "Empresa",
        "N° asistentes", "Lista asistencia", "Evaluación", "Evidencia", "Observaciones",
    ]
    ws.append(headers)
    style_header_row(ws, 1, len(headers))
    col, n = listas_named["temas_cap"]
    dv = dv_list(list_range("_Listas", col, n))
    ws.add_data_validation(dv)
    dv.add(f"B2:B200")
    add_table(ws, "TablaCapacitaciones", f"A1:{get_column_letter(len(headers))}200")
    ws.freeze_panes = "A2"
    auto_width(ws)
    return ws


def build_fotos(wb):
    ws = wb.create_sheet("Registro fotográfico")
    headers = [
        "ID foto", "Fecha", "Mes", "Ubicación", "Componente ambiental", "Descripción",
        "Tipo evidencia", "Antes/después", "Nombre archivo", "Enlace", "Coordenadas",
        "Responsable", "Observaciones",
    ]
    ws.append(headers)
    style_header_row(ws, 1, len(headers))
    for i in range(2, 102):
        ws.cell(i, 1, f"FOT-{i-1:03d}")
        ws.cell(i, 3, "=Config!B2")
    add_table(ws, "TablaFotos", f"A1:{get_column_letter(len(headers))}101")
    ws.freeze_panes = "A2"
    auto_width(ws)
    return ws


def build_dashboard(wb, n_matriz):
    ws = wb.create_sheet("Dashboard")
    ws["A1"] = "DASHBOARD MENSUAL — AUDITORÍA AMBIENTAL"
    ws["A1"].font = Font(bold=True, size=14, color=C_AZUL)
    ws["A2"] = "Periodo:"
    ws["B2"] = "=Config!B2"

    labels = [
        ("A4", "% cumplimiento total", "B4"),
        ("A5", "% requisitos cumplidos", "B5"),
        ("A6", "% cumplimiento parcial", "B6"),
        ("A7", "Incumplimientos (No cumple)", "B7"),
        ("A8", "Hallazgos críticos", "B8"),
        ("A9", "Hallazgos mayores", "B9"),
        ("A10", "Hallazgos abiertos", "B10"),
        ("A11", "Hallazgos vencidos", "B11"),
        ("A12", "Documentos vigentes", "B12"),
        ("A13", "Documentos por vencer (≤60 d)", "B13"),
        ("A14", "Documentos vencidos", "B14"),
        ("A15", "Capacitaciones del mes", "B15"),
        ("A16", "Reclamos comunitarios", "B16"),
        ("A17", "Incidentes ambientales", "B17"),
        ("A18", "Controles ejecutados", "B18"),
        ("A19", "Semáforo cumplimiento", "B19"),
    ]
    mat = "Matriz auditoría mensual"
    hal = "Registro hallazgos"
    doc = "Control permisos"
    cap = "Capacitaciones"
    for lbl_cell, lbl, val_cell in labels:
        ws[lbl_cell] = lbl
        ws[lbl_cell].font = Font(bold=True)

    ws["B4"] = (
        f'=SI.ERROR('
        f'(CONTAR.SI(\'{mat}\'!N2:N{n_matriz};"Cumple")*Config!$B$9+'
        f'CONTAR.SI(\'{mat}\'!N2:N{n_matriz};"Cumple parcialmente")*Config!$B$10+'
        f'CONTAR.SI(\'{mat}\'!N2:N{n_matriz};"No cumple")*Config!$B$11+'
        f'CONTAR.SI(\'{mat}\'!N2:N{n_matriz};"En proceso de regularización")*Config!$B$12)/'
        f'(CONTAR(\'{mat}\'!N2:N{n_matriz})-CONTAR.SI(\'{mat}\'!N2:N{n_matriz};"No aplica")-'
        f'CONTAR.SI(\'{mat}\'!N2:N{n_matriz};"Pendiente de verificación"));0)'
    )
    ws["B5"] = f'=CONTAR.SI(\'{mat}\'!N2:N{n_matriz};"Cumple")'
    ws["B6"] = f'=CONTAR.SI(\'{mat}\'!N2:N{n_matriz};"Cumple parcialmente")'
    ws["B7"] = f'=CONTAR.SI(\'{mat}\'!N2:N{n_matriz};"No cumple")'
    ws["B8"] = f'=CONTAR.SI.CONJUNTO(\'{hal}\'!H:H;"Crítico";\'{hal}\'!P:P;"<>Cerrado")'
    ws["B9"] = f'=CONTAR.SI.CONJUNTO(\'{hal}\'!H:H;"Mayor";\'{hal}\'!P:P;"<>Cerrado")'
    ws["B10"] = f'=CONTAR.SI(\'{hal}\'!P:P;"Abierto")+CONTAR.SI(\'{hal}\'!P:P;"En tratamiento")'
    ws["B11"] = f'=CONTAR.SI.CONJUNTO(\'{hal}\'!N:N;"<"&HOY();\'{hal}\'!O:O;"")'
    ws["B12"] = f'=CONTAR.SI(\'{doc}\'!K:K;"Vigente")'
    ws["B13"] = f'=CONTAR.SI(\'{doc}\'!K:K;"Por vencer en 30 días")+CONTAR.SI(\'{doc}\'!K:K;"Por vencer en 60 días")'
    ws["B14"] = f'=CONTAR.SI(\'{doc}\'!K:K;"Vencido")'
    ws["B15"] = f'=CONTAR(\'{cap}\'!A2:A200)'
    ws["B16"] = f'=CONTAR.SI(\'{mat}\'!AB:AB;"*reclamo*")'
    ws["B17"] = f'=CONTAR.SI(\'{hal}\'!H:H;"Crítico")'
    ws["B18"] = f'=CONTAR(\'{mat}\'!T2:T{n_matriz})'
    ws["B19"] = '=SI(B4>=0,9;"VERDE";SI(B4>=0,7;"AMARILLO";"ROJO"))'

    for r in range(4, 20):
        ws.cell(r, 2).border = BORDER
        if r == 4:
            ws.cell(r, 2).number_format = "0.00%"

    # Tabla resumen estados para gráfico
    ws["D4"] = "Estado"
    ws["E4"] = "Cantidad"
    ws["D5"], ws["E5"] = "Cumple", f'=CONTAR.SI(\'{mat}\'!N2:N{n_matriz};"Cumple")'
    ws["D6"], ws["E6"] = "Cumple parcialmente", f'=CONTAR.SI(\'{mat}\'!N2:N{n_matriz};"Cumple parcialmente")'
    ws["D7"], ws["E7"] = "No cumple", f'=CONTAR.SI(\'{mat}\'!N2:N{n_matriz};"No cumple")'
    ws["D8"], ws["E8"] = "Pendiente", f'=CONTAR.SI(\'{mat}\'!N2:N{n_matriz};"Pendiente de verificación")'
    ws["D9"], ws["E9"] = "En regularización", f'=CONTAR.SI(\'{mat}\'!N2:N{n_matriz};"En proceso de regularización")'

    pie = PieChart()
    pie.title = "Distribución estados de cumplimiento"
    pie.add_data(Reference(ws, min_col=5, min_row=5, max_row=9), titles_from_data=False)
    pie.set_categories(Reference(ws, min_col=4, min_row=5, max_row=9))
    pie.width = 14
    pie.height = 10
    ws.add_chart(pie, "G4")

    # Hallazgos por nivel
    ws["D12"] = "Nivel hallazgo"
    ws["E12"] = "Cantidad"
    niveles = ["Crítico", "Mayor", "Menor", "Observación", "Buena práctica"]
    for i, nv in enumerate(niveles, 13):
        ws.cell(i, 4, nv)
        ws.cell(i, 5, f'=CONTAR.SI(\'{hal}\'!H:H;"{nv}")')
    bar = BarChart()
    bar.type = "col"
    bar.title = "Hallazgos por nivel"
    bar.add_data(Reference(ws, min_col=5, min_row=13, max_row=17), titles_from_data=False)
    bar.set_categories(Reference(ws, min_col=4, min_row=13, max_row=17))
    bar.width = 14
    bar.height = 10
    ws.add_chart(bar, "G18")

    ws.column_dimensions["A"].width = 32
    ws.column_dimensions["B"].width = 18
    return ws


def build_informe(wb, n_matriz):
    ws = wb.create_sheet("Informe mensual")
    ws["A1"] = "INFORME MENSUAL AUTOMÁTICO — RESUMEN EJECUTIVO"
    ws["A1"].font = FONT_TITLE
    fields = [
        ("Periodo auditado:", "=Config!B2"),
        ("Estado general:", "=Dashboard!B19"),
        ("Porcentaje cumplimiento:", "=Dashboard!B4"),
        ("Principales cumplimientos:", "(Completar manualmente a partir de la matriz)"),
        ("Principales incumplimientos:", "(Completar manualmente a partir de la matriz)"),
        ("Hallazgos críticos y mayores:", "=Dashboard!B8 & \" críticos; \" & Dashboard!B9 & \" mayores\""),
        ("Acciones correctivas pendientes:", "=Dashboard!B10"),
        ("Documentos vencidos o por vencer:", "=Dashboard!B13 & \" por vencer; \" & Dashboard!B14 & \" vencidos\""),
        ("Residuos generados:", "(Ver hoja Registro residuos)"),
        ("Capacitaciones realizadas:", "=Dashboard!B15"),
        ("Incidentes ambientales:", "(Ver Registro hallazgos / Matriz REQ-038)"),
        ("Reclamos comunitarios:", "(Ver Matriz REQ-027, REQ-078)"),
        ("Recomendaciones:", ""),
        ("Conclusión del auditor:", ""),
        ("Nombre y firma:", "=Config!B5"),
    ]
    r = 3
    for label, val in fields:
        ws.cell(r, 1, label).font = Font(bold=True)
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=6)
        c = ws.cell(r, 2, val)
        c.alignment = Alignment(wrap_text=True, vertical="top")
        c.border = BORDER
        ws.row_dimensions[r].height = 28 if r > 5 else 20
        r += 1
    ws.column_dimensions["A"].width = 30
    ws.column_dimensions["B"].width = 80
    return ws


def protect_formulas(wb):
    for ws in wb.worksheets:
        if ws.title.startswith("_"):
            continue
        ws.protection.sheet = False


def main():
    wb = Workbook()
    wb.remove(wb.active)
    listas_ws, listas_named = build_listas(wb)
    build_portada(wb)
    build_config(wb, listas_named)
    build_instrucciones(wb)
    _, n_cat = build_catalogo(wb, listas_named)
    _, n_matriz = build_matriz(wb, listas_named, len(REQUISITOS))
    build_hallazgos(wb, listas_named)
    build_documentos(wb, listas_named)
    build_residuos(wb, listas_named)
    build_agua(wb)
    build_capacitaciones(wb, listas_named)
    build_fotos(wb)
    build_dashboard(wb, n_matriz)
    build_informe(wb, n_matriz)
    protect_formulas(wb)
    wb.save(OUTPUT)
    print(f"Generado: {OUTPUT}")
    print(f"Requisitos en catálogo: {len(REQUISITOS)}")


if __name__ == "__main__":
    main()

/*
 * Gerador de planilhas .xlsx sem nenhuma dependência externa.
 *
 * Cria um pacote OOXML mínimo (algumas partes XML + um .zip sem compressão)
 * suficiente para o Excel, LibreOffice Calc e Google Sheets abrirem
 * corretamente. Não usa nenhuma biblioteca de terceiros — importante para
 * este ser um sistema 100% local, sem precisar baixar nada da internet.
 */

const XlsxWriter = (() => {

  // ---------------- ZIP (armazenamento sem compressão) ----------------

  const CRC_TABLE = (() => {
    const table = new Uint32Array(256);
    for (let n = 0; n < 256; n++) {
      let c = n;
      for (let k = 0; k < 8; k++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
      table[n] = c >>> 0;
    }
    return table;
  })();

  function crc32(bytes) {
    let crc = 0xFFFFFFFF;
    for (let i = 0; i < bytes.length; i++) {
      crc = CRC_TABLE[(crc ^ bytes[i]) & 0xFF] ^ (crc >>> 8);
    }
    return (crc ^ 0xFFFFFFFF) >>> 0;
  }

  function u16(n) { return new Uint8Array([n & 0xFF, (n >>> 8) & 0xFF]); }
  function u32(n) { return new Uint8Array([n & 0xFF, (n >>> 8) & 0xFF, (n >>> 16) & 0xFF, (n >>> 24) & 0xFF]); }
  function strBytes(s) { return new TextEncoder().encode(s); }

  function concat(arrays) {
    let total = 0;
    arrays.forEach(a => total += a.length);
    const out = new Uint8Array(total);
    let offset = 0;
    arrays.forEach(a => { out.set(a, offset); offset += a.length; });
    return out;
  }

  function dosDateTime(date) {
    const time = u16(((date.getHours() & 0x1F) << 11) | ((date.getMinutes() & 0x3F) << 5) | ((date.getSeconds() >> 1) & 0x1F));
    const yr = Math.max(0, date.getFullYear() - 1980);
    const dt = u16(((yr & 0x7F) << 9) | (((date.getMonth() + 1) & 0xF) << 5) | (date.getDate() & 0x1F));
    return { time, dt };
  }

  /** files: [{ name: 'xl/workbook.xml', data: Uint8Array }] -> Uint8Array (arquivo .zip completo) */
  function buildZip(files) {
    const now = new Date();
    const { time, dt } = dosDateTime(now);
    const localParts = [];
    const centralParts = [];
    let offset = 0;

    files.forEach(file => {
      const nameBytes = strBytes(file.name);
      const crc = crc32(file.data);
      const size = u32(file.data.length);

      const localHeader = concat([
        u32(0x04034b50), u16(20), u16(0), u16(0), time, dt,
        u32(crc), size, size, u16(nameBytes.length), u16(0)
      ]);
      const localEntry = concat([localHeader, nameBytes, file.data]);
      localParts.push(localEntry);

      const centralHeader = concat([
        u32(0x02014b50), u16(20), u16(20), u16(0), u16(0), time, dt,
        u32(crc), size, size, u16(nameBytes.length), u16(0), u16(0), u16(0), u16(0), u32(0),
        u32(offset)
      ]);
      centralParts.push(concat([centralHeader, nameBytes]));

      offset += localEntry.length;
    });

    const centralDir = concat(centralParts);
    const localAll = concat(localParts);
    const eocd = concat([
      u32(0x06054b50), u16(0), u16(0),
      u16(files.length), u16(files.length),
      u32(centralDir.length), u32(localAll.length), u16(0)
    ]);

    return concat([localAll, centralDir, eocd]);
  }

  // ---------------- Conteúdo OOXML da planilha ----------------

  function xmlEscape(str) {
    return String(str ?? '')
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&apos;');
  }

  function colLetter(n) {
    let s = '';
    n = n + 1;
    while (n > 0) {
      const rem = (n - 1) % 26;
      s = String.fromCharCode(65 + rem) + s;
      n = Math.floor((n - 1) / 26);
    }
    return s;
  }

  function celulaXml(valor, colIdx, rowIdx) {
    const ref = `${colLetter(colIdx)}${rowIdx}`;
    if (typeof valor === 'number' && isFinite(valor)) {
      return `<c r="${ref}"><v>${valor}</v></c>`;
    }
    return `<c r="${ref}" t="inlineStr"><is><t xml:space="preserve">${xmlEscape(valor)}</t></is></c>`;
  }

  function sheetXml(colunas, linhas) {
    let rows = '';
    rows += `<row r="1">${colunas.map((c, i) => celulaXml(c, i, 1)).join('')}</row>`;
    linhas.forEach((linha, li) => {
      const r = li + 2;
      rows += `<row r="${r}">${linha.map((v, i) => celulaXml(v, i, r)).join('')}</row>`;
    });
    const largura = Math.max(10, ...colunas.map(c => Math.min(45, String(c).length + 4)));
    return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<cols><col min="1" max="${Math.max(1, colunas.length)}" width="${largura}" customWidth="1"/></cols>
<sheetData>${rows}</sheetData>
</worksheet>`;
  }

  function sanitizeSheetName(nome, indice) {
    let s = String(nome || `Planilha${indice + 1}`).replace(/[:\\/?*\[\]]/g, ' ').trim();
    if (!s) s = `Planilha${indice + 1}`;
    return s.slice(0, 31);
  }

  /**
   * planilhas: [{ nome: 'Atividades', colunas: ['A','B'], linhas: [[1,'x'], ...] }]
   * Retorna um Blob pronto para download.
   */
  function gerarBlob(planilhas) {
    const nomesSheets = planilhas.map((p, i) => sanitizeSheetName(p.nome, i));

    const contentTypes = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
${planilhas.map((_, i) => `<Override PartName="/xl/worksheets/sheet${i + 1}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>`).join('\n')}
</Types>`;

    const rootRels = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>`;

    const workbook = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheets>
${nomesSheets.map((nome, i) => `<sheet name="${xmlEscape(nome)}" sheetId="${i + 1}" r:id="rId${i + 1}"/>`).join('\n')}
</sheets>
</workbook>`;

    const workbookRels = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
${planilhas.map((_, i) => `<Relationship Id="rId${i + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet${i + 1}.xml"/>`).join('\n')}
</Relationships>`;

    const files = [
      { name: '[Content_Types].xml', data: strBytes(contentTypes) },
      { name: '_rels/.rels', data: strBytes(rootRels) },
      { name: 'xl/workbook.xml', data: strBytes(workbook) },
      { name: 'xl/_rels/workbook.xml.rels', data: strBytes(workbookRels) }
    ];
    planilhas.forEach((p, i) => {
      files.push({ name: `xl/worksheets/sheet${i + 1}.xml`, data: strBytes(sheetXml(p.colunas, p.linhas)) });
    });

    const zipBytes = buildZip(files);
    return new Blob([zipBytes], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
  }

  function baixar(planilhas, nomeArquivo) {
    const blob = gerarBlob(planilhas);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = nomeArquivo.endsWith('.xlsx') ? nomeArquivo : `${nomeArquivo}.xlsx`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  return { gerarBlob, baixar };
})();

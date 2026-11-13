function escapeCell(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

function cellXml(value) {
  const text = value ?? ''
  const numeric = typeof text === 'number' || (typeof text === 'string' && /^-?\d+(\.\d+)?$/.test(text))
  const type = numeric ? 'Number' : 'String'
  return `<Cell><Data ss:Type="${type}">${escapeCell(text)}</Data></Cell>`
}

export function downloadExcel(filename, headers, rows) {
  const head = headers.map((item) => cellXml(item)).join('')
  const body = rows.map((row) => `<Row>${row.map((item) => cellXml(item)).join('')}</Row>`).join('')
  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<?mso-application progid="Excel.Sheet"?>
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet" xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">
<Worksheet ss:Name="报销台账"><Table>
<Row>${head}</Row>
${body}
</Table></Worksheet>
</Workbook>`
  const blob = new Blob([xml], { type: 'application/vnd.ms-excel;charset=utf-8' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  window.URL.revokeObjectURL(url)
}

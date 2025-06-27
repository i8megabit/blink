import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card'
import { Button } from './ui/Button'
import { Badge } from './ui/Badge'

interface ExportFormat {
  id: string
  name: string
  description: string
  icon: string
  extension: string
}

interface ExportProps {
  recommendations: Array<{
    from: string
    to: string
    anchor: string
    comment: string
  }>
  domain: string
  onExport?: (format: string, data: string) => void
}

const EXPORT_FORMATS: ExportFormat[] = [
  {
    id: 'csv',
    name: 'CSV',
    description: 'Таблица для Excel/Google Sheets',
    icon: '📊',
    extension: '.csv'
  },
  {
    id: 'json',
    name: 'JSON',
    description: 'Структурированные данные',
    icon: '🔧',
    extension: '.json'
  },
  {
    id: 'html',
    name: 'HTML',
    description: 'Готовая разметка для сайта',
    icon: '🌐',
    extension: '.html'
  },
  {
    id: 'txt',
    name: 'Текст',
    description: 'Простой текстовый формат',
    icon: '📝',
    extension: '.txt'
  }
]

const Export: React.FC<ExportProps> = ({ 
  recommendations, 
  domain, 
  onExport 
}) => {
  const [selectedFormat, setSelectedFormat] = useState<string>('csv')
  const [isExporting, setIsExporting] = useState(false)

  const generateCSV = (): string => {
    const headers = ['Источник', 'Цель', 'Анкор', 'Обоснование']
    const rows = recommendations.map(rec => [
      rec.from,
      rec.to,
      rec.anchor,
      rec.comment
    ])
    
    return [headers, ...rows]
      .map(row => row.map(cell => `"${cell.replace(/"/g, '""')}"`).join(','))
      .join('\n')
  }

  const generateJSON = (): string => {
    return JSON.stringify({
      domain,
      exportDate: new Date().toISOString(),
      totalRecommendations: recommendations.length,
      recommendations: recommendations.map(rec => ({
        source: rec.from,
        target: rec.to,
        anchor: rec.anchor,
        reasoning: rec.comment
      }))
    }, null, 2)
  }

  const generateHTML = (): string => {
    const rows = recommendations.map(rec => `
      <tr>
        <td><a href="${rec.from}" target="_blank">${rec.from}</a></td>
        <td><a href="${rec.to}" target="_blank">${rec.to}</a></td>
        <td>${rec.anchor}</td>
        <td>${rec.comment}</td>
      </tr>
    `).join('')

    return `
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SEO Рекомендации - ${domain}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        a { color: #0066cc; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .header { background-color: #f8f9fa; padding: 20px; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>SEO Рекомендации</h1>
        <p><strong>Домен:</strong> ${domain}</p>
        <p><strong>Дата экспорта:</strong> ${new Date().toLocaleDateString('ru-RU')}</p>
        <p><strong>Всего рекомендаций:</strong> ${recommendations.length}</p>
    </div>
    
    <table>
        <thead>
            <tr>
                <th>Источник</th>
                <th>Цель</th>
                <th>Анкор</th>
                <th>Обоснование</th>
            </tr>
        </thead>
        <tbody>
            ${rows}
        </tbody>
    </table>
</body>
</html>`
  }

  const generateTXT = (): string => {
    return `SEO Рекомендации для ${domain}
Дата экспорта: ${new Date().toLocaleDateString('ru-RU')}
Всего рекомендаций: ${recommendations.length}

${recommendations.map((rec, index) => `
${index + 1}. ${rec.from} → ${rec.to}
   Анкор: ${rec.anchor}
   Обоснование: ${rec.comment}
`).join('\n')}`
  }

  const handleExport = async () => {
    if (!recommendations.length) return

    setIsExporting(true)
    
    try {
      let data = ''
      let filename = `seo-recommendations-${domain}-${new Date().toISOString().split('T')[0]}`

      switch (selectedFormat) {
        case 'csv':
          data = generateCSV()
          filename += '.csv'
          break
        case 'json':
          data = generateJSON()
          filename += '.json'
          break
        case 'html':
          data = generateHTML()
          filename += '.html'
          break
        case 'txt':
          data = generateTXT()
          filename += '.txt'
          break
        default:
          data = generateCSV()
          filename += '.csv'
      }

      // Создаем и скачиваем файл
      const blob = new Blob([data], { 
        type: selectedFormat === 'json' ? 'application/json' : 
              selectedFormat === 'html' ? 'text/html' : 
              selectedFormat === 'csv' ? 'text/csv' : 'text/plain'
      })
      
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)

      // Вызываем callback если предоставлен
      if (onExport) {
        onExport(selectedFormat, data)
      }

    } catch (error) {
      console.error('Ошибка экспорта:', error)
    } finally {
      setIsExporting(false)
    }
  }

  if (!recommendations.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Экспорт данных</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <div className="text-4xl mb-4">📤</div>
            <p>Нет данных для экспорта</p>
            <p className="text-sm">Сначала выполните анализ домена</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">Экспорт данных</CardTitle>
        <p className="text-sm text-muted-foreground">
          Выберите формат для экспорта {recommendations.length} рекомендаций
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Выбор формата */}
        <div className="grid grid-cols-2 gap-3">
          {EXPORT_FORMATS.map((format) => (
            <button
              key={format.id}
              onClick={() => setSelectedFormat(format.id)}
              className={`p-4 border rounded-lg text-left transition-all ${
                selectedFormat === format.id
                  ? 'border-primary bg-primary/5'
                  : 'border-border hover:border-primary/50'
              }`}
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">{format.icon}</span>
                <div>
                  <div className="font-medium">{format.name}</div>
                  <div className="text-sm text-muted-foreground">
                    {format.description}
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>

        {/* Информация о выбранном формате */}
        <div className="p-4 bg-muted rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">
                {EXPORT_FORMATS.find(f => f.id === selectedFormat)?.name}
              </div>
              <div className="text-sm text-muted-foreground">
                {EXPORT_FORMATS.find(f => f.id === selectedFormat)?.description}
              </div>
            </div>
            <Badge variant="secondary">
              {recommendations.length} рекомендаций
            </Badge>
          </div>
        </div>

        {/* Кнопка экспорта */}
        <Button
          onClick={handleExport}
          disabled={isExporting}
          className="w-full"
        >
          {isExporting ? (
            <>
              <svg className="animate-spin -ml-1 mr-3 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Экспорт...
            </>
          ) : (
            <>
              📥 Экспортировать в {EXPORT_FORMATS.find(f => f.id === selectedFormat)?.name}
            </>
          )}
        </Button>

        {/* Дополнительные опции */}
        <div className="text-xs text-muted-foreground text-center">
          Файл будет автоматически скачан в папку загрузок
        </div>
      </CardContent>
    </Card>
  )
}

export default Export 
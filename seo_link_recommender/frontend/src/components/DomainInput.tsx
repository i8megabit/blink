import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { Input } from './ui/Input';
import { Button } from './ui/Button';
import { Badge } from './ui/Badge';
import { cn } from '../lib/utils';
import { 
  Globe, 
  Search, 
  AlertCircle, 
  CheckCircle,
  Play,
  Settings
} from 'lucide-react';

interface DomainInputProps {
  onAnalyze: (domain: string, comprehensive: boolean) => void;
  isLoading?: boolean;
  className?: string;
}

export function DomainInput({ onAnalyze, isLoading, className }: DomainInputProps) {
  const [domain, setDomain] = useState('');
  const [comprehensive, setComprehensive] = useState(true);
  const [error, setError] = useState('');

  const validateDomain = (value: string): boolean => {
    if (!value.trim()) {
      setError('Введите домен');
      return false;
    }

    // Простая валидация домена
    const domainRegex = /^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
    if (!domainRegex.test(value)) {
      setError('Некорректный формат домена');
      return false;
    }

    setError('');
    return true;
  };

  const handleDomainChange = (value: string) => {
    setDomain(value);
    if (error) {
      validateDomain(value);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (validateDomain(domain)) {
      onAnalyze(domain.trim(), comprehensive);
    }
  };

  const handleQuickAnalyze = (quickDomain: string) => {
    setDomain(quickDomain);
    onAnalyze(quickDomain, comprehensive);
  };

  const quickDomains = [
    'example.com',
    'test.ru',
    'demo.org'
  ];

  return (
    <div className={cn("space-y-4", className)}>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="w-5 h-5" />
            Анализ домена
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Input
                label="Домен для анализа"
                placeholder="example.com"
                value={domain}
                onChange={(e) => handleDomainChange(e.target.value)}
                error={error}
                leftIcon={<Search className="w-4 h-4" />}
                disabled={isLoading}
                helperText="Введите домен без http:// или https://"
              />
            </div>

            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={comprehensive}
                  onChange={(e) => setComprehensive(e.target.checked)}
                  disabled={isLoading}
                  className="rounded border-gray-300"
                />
                <span className="text-sm">Полный анализ</span>
                <Badge variant="outline" className="text-xs">
                  Рекомендуется
                </Badge>
              </label>
            </div>

            <div className="flex gap-2">
              <Button
                type="submit"
                disabled={isLoading || !domain.trim()}
                className="flex-1"
              >
                {isLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                    Анализирую...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2" />
                    Начать анализ
                  </>
                )}
              </Button>
              
              <Button
                type="button"
                variant="outline"
                onClick={() => setComprehensive(!comprehensive)}
                disabled={isLoading}
              >
                <Settings className="w-4 h-4" />
              </Button>
            </div>
          </form>

          {/* Быстрый анализ */}
          <div className="pt-4 border-t">
            <h4 className="text-sm font-medium mb-3">Быстрый анализ:</h4>
            <div className="flex flex-wrap gap-2">
              {quickDomains.map((quickDomain) => (
                <Button
                  key={quickDomain}
                  variant="outline"
                  size="sm"
                  onClick={() => handleQuickAnalyze(quickDomain)}
                  disabled={isLoading}
                  className="text-xs"
                >
                  {quickDomain}
                </Button>
              ))}
            </div>
          </div>

          {/* Информация о режимах */}
          <div className="pt-4 border-t">
            <div className="space-y-2">
              <div className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 text-green-500 mt-0.5" />
                <div className="text-sm">
                  <span className="font-medium">Полный анализ:</span>
                  <span className="text-muted-foreground ml-1">
                    Семантический анализ, кластеризация, кумулятивные рекомендации
                  </span>
                </div>
              </div>
              <div className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-orange-500 mt-0.5" />
                <div className="text-sm">
                  <span className="font-medium">Базовый анализ:</span>
                  <span className="text-muted-foreground ml-1">
                    Простая индексация и генерация ссылок
                  </span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
} 
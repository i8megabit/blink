import { useState } from 'react';
import { Domain } from '../types';
import { Card, CardContent } from './ui/Card';
import { Button } from './ui/Button';
import { Badge } from './ui/Badge';
import { cn } from '../lib/utils';
import { 
  Globe,
  FileText,
  Link,
  Timer,
  CheckCircle,
  Play,
  Eye,
  Trash2,
  RefreshCw,
  Download
} from 'lucide-react';

interface DomainsListProps {
  domains: Domain[];
  onAnalyze: (domain: string, comprehensive: boolean) => void;
  onDelete?: (domainId: number) => void;
  onViewHistory?: (domainId: number) => void;
  isLoading?: boolean;
  className?: string;
}

export function DomainsList({ 
  domains, 
  onAnalyze, 
  onDelete, 
  onViewHistory,
  isLoading, 
  className 
}: DomainsListProps) {
  const [expandedDomain, setExpandedDomain] = useState<number | null>(null);

  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return 'Не анализировался';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return 'Только что';
    if (diffInHours < 24) return `${diffInHours}ч назад`;
    if (diffInHours < 168) return `${Math.floor(diffInHours / 24)}д назад`;
    
    return date.toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  const getStatusBadge = (domain: Domain) => {
    if (!domain.is_indexed) {
      return <Badge variant="secondary">Не индексирован</Badge>;
    }
    
    if (!domain.last_analysis_at) {
      return <Badge variant="outline">Требует анализа</Badge>;
    }
    
    const lastAnalysis = new Date(domain.last_analysis_at);
    const now = new Date();
    const diffInDays = Math.floor((now.getTime() - lastAnalysis.getTime()) / (1000 * 60 * 60 * 24));
    
    if (diffInDays < 7) {
      return <Badge variant="default" className="bg-green-100 text-green-800">Актуальный</Badge>;
    } else if (diffInDays < 30) {
      return <Badge variant="outline" className="text-yellow-600">Устарел</Badge>;
    } else {
      return <Badge variant="destructive">Сильно устарел</Badge>;
    }
  };

  const getDomainIcon = (domain: Domain) => {
    if (!domain.is_indexed) {
      return <Globe className="w-4 h-4 text-gray-400" />;
    }
    
    if (domain.total_posts > 100) {
      return <Globe className="w-4 h-4 text-green-500" />;
    } else if (domain.total_posts > 50) {
      return <Globe className="w-4 h-4 text-blue-500" />;
    } else {
      return <Globe className="w-4 h-4 text-orange-500" />;
    }
  };

  if (domains.length === 0) {
    return (
      <Card className={className}>
        <CardContent className="flex flex-col items-center justify-center py-12">
          <Globe className="w-12 h-12 text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Нет доменов</h3>
          <p className="text-gray-500 text-center mb-4">
            Добавьте первый домен для анализа и получения рекомендаций по внутренним ссылкам
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Домены ({domains.length})</h2>
        <Badge variant="outline">
          {domains.filter(d => d.is_indexed).length} проиндексировано
        </Badge>
      </div>

      <div className="space-y-3">
        {domains.map((domain) => (
          <Card key={domain.id} className="hover:shadow-md transition-shadow">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 flex-1">
                  {getDomainIcon(domain)}
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-medium truncate">{domain.display_name || domain.name}</h3>
                      {getStatusBadge(domain)}
                    </div>
                    
                    <div className="flex items-center gap-4 text-sm text-gray-500">
                      <div className="flex items-center gap-1">
                        <FileText className="w-4 h-4" />
                        <span>{domain.total_posts} статей</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Timer className="w-4 h-4" />
                        <span>
                          {domain.last_analysis_at 
                            ? new Date(domain.last_analysis_at).toLocaleDateString('ru-RU')
                            : 'Не анализировался'
                          }
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {onViewHistory && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onViewHistory(domain.id)}
                      title="История анализов"
                    >
                      <Eye className="w-4 h-4" />
                    </Button>
                  )}
                  
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onAnalyze(domain.name, true)}
                    disabled={isLoading}
                    title="Повторный анализ"
                  >
                    <RefreshCw className="w-4 h-4" />
                  </Button>
                  
                  {onDelete && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onDelete(domain.id)}
                      disabled={isLoading}
                      className="text-red-500 hover:text-red-700"
                      title="Удалить домен"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              </div>

              {/* Расширенная информация */}
              {expandedDomain === domain.id && (
                <div className="mt-4 pt-4 border-t space-y-3">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">
                        {domain.total_posts}
                      </div>
                      <div className="text-xs text-muted-foreground">Статей</div>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">
                        {domain.total_analyses}
                      </div>
                      <div className="text-xs text-muted-foreground">Анализов</div>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-2xl font-bold text-purple-600">
                        {domain.language.toUpperCase()}
                      </div>
                      <div className="text-xs text-muted-foreground">Язык</div>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-2xl font-bold text-orange-600">
                        {formatDate(domain.updated_at)}
                      </div>
                      <div className="text-xs text-muted-foreground">Обновлен</div>
                    </div>
                  </div>
                  
                  {domain.description && (
                    <div className="text-sm text-muted-foreground">
                      {domain.description}
                    </div>
                  )}
                  
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onAnalyze(domain.name, true)}
                      className="flex items-center"
                    >
                      <CheckCircle className="w-4 h-4 mr-2" />
                      Анализировать
                    </Button>
                  </div>
                </div>
              )}

              {/* Кнопка расширения */}
              <div className="mt-3 pt-3 border-t">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setExpandedDomain(
                    expandedDomain === domain.id ? null : domain.id
                  )}
                  className="w-full text-muted-foreground"
                >
                  {expandedDomain === domain.id ? 'Скрыть детали' : 'Показать детали'}
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
} 
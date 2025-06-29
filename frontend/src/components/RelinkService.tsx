import React, { useState, useEffect } from 'react';
import { Card, Button, Badge, Input, Modal } from './ui';

interface RelinkServiceProps {
  serviceName: string;
  description: string;
}

interface AnalysisResult {
  domain: string;
  total_posts: number;
  internal_links: number;
  recommendations: string[];
  status: string;
}

export const RelinkService: React.FC<RelinkServiceProps> = ({
  serviceName,
  description
}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [domain, setDomain] = useState('dagorod.ru');
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [showModal, setShowModal] = useState(false);

  const testConnection = async () => {
    try {
      const response = await fetch(`http://localhost:3000/api/relink/health`);
      setIsConnected(response.ok);
    } catch (error) {
      setIsConnected(false);
    }
  };

  const analyzeDomain = async () => {
    if (!domain.trim()) return;

    setIsAnalyzing(true);
    try {
      const response = await fetch(`http://localhost:3000/api/relink/analyze-dagorod`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ domain: domain.trim() }),
      });

      if (response.ok) {
        const result = await response.json();
        setAnalysisResult(result);
        setShowModal(true);
      } else {
        console.error('Analysis failed:', response.statusText);
      }
    } catch (error) {
      console.error('Analysis error:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const getDashboard = async () => {
    if (!domain.trim()) return;

    try {
      const response = await fetch(`http://localhost:3000/api/relink/dashboard/${domain.trim()}`);
      if (response.ok) {
        const dashboard = await response.json();
        setAnalysisResult(dashboard);
        setShowModal(true);
      }
    } catch (error) {
      console.error('Dashboard error:', error);
    }
  };

  useEffect(() => {
    testConnection();
  }, []);

  return (
    <>
      <Card>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold">{serviceName}</h3>
            <p className="text-gray-600">{description}</p>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant={isConnected ? "success" : "error"}>
              {isConnected ? "Connected" : "Disconnected"}
            </Badge>
            <Button onClick={testConnection} size="sm">
              Test
            </Button>
            <Button 
              onClick={() => window.open(`http://localhost:8001/docs`, '_blank')}
              size="sm"
              variant="outline"
            >
              Swagger
            </Button>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Домен для анализа
            </label>
            <Input
              value={domain}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setDomain(e.target.value)}
              placeholder="Введите домен (например: dagorod.ru)"
              className="w-full"
            />
          </div>

          <div className="flex space-x-2">
            <Button 
              onClick={analyzeDomain}
              disabled={isAnalyzing || !domain.trim()}
              className="flex-1"
            >
              {isAnalyzing ? 'Анализируем...' : 'Полный анализ'}
            </Button>
            <Button 
              onClick={getDashboard}
              disabled={!domain.trim()}
              variant="outline"
              className="flex-1"
            >
              Дашборд
            </Button>
          </div>
        </div>
      </Card>

      <Modal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title="Результаты анализа reLink"
      >
        {analysisResult && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-50 p-3 rounded">
                <div className="text-sm text-gray-600">Домен</div>
                <div className="font-semibold">{analysisResult.domain}</div>
              </div>
              <div className="bg-gray-50 p-3 rounded">
                <div className="text-sm text-gray-600">Статус</div>
                <div className="font-semibold">{analysisResult.status}</div>
              </div>
              <div className="bg-gray-50 p-3 rounded">
                <div className="text-sm text-gray-600">Постов</div>
                <div className="font-semibold">{analysisResult.total_posts}</div>
              </div>
              <div className="bg-gray-50 p-3 rounded">
                <div className="text-sm text-gray-600">Внутренних ссылок</div>
                <div className="font-semibold">{analysisResult.internal_links}</div>
              </div>
            </div>

            {analysisResult.recommendations && analysisResult.recommendations.length > 0 && (
              <div>
                <h4 className="font-semibold mb-2">SEO рекомендации:</h4>
                <ul className="space-y-2">
                  {analysisResult.recommendations.map((rec, index) => (
                    <li key={index} className="text-sm bg-blue-50 p-2 rounded">
                      {rec}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </Modal>
    </>
  );
}; 
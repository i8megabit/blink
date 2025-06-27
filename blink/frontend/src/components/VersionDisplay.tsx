import React, { useState, useEffect } from 'react';

interface VersionInfo {
  version: string;
  buildDate: string;
  commitHash?: string;
}

const VersionDisplay: React.FC = () => {
  const [versionInfo, setVersionInfo] = useState<VersionInfo>({
    version: '3.0.17',
    buildDate: new Date().toISOString().split('T')[0] || 'unknown'
  });

  useEffect(() => {
    // В продакшене можно загружать версию из API или переменных окружения
    const loadVersionInfo = async () => {
      try {
        // Попытка загрузить версию из API
        const response = await fetch('/api/v1/version');
        if (response.ok) {
          const data = await response.json();
          setVersionInfo(data);
        }
      } catch (error) {
        // Используем значения по умолчанию
        console.log('Используем версию по умолчанию');
      }
    };

    loadVersionInfo();
  }, []);

  return (
    <div className="flex items-center gap-2 text-xs text-muted-foreground">
      <span className="font-mono">v{versionInfo.version}</span>
      <span className="text-gray-400">•</span>
      <span>{versionInfo.buildDate}</span>
      {versionInfo.commitHash && (
        <>
          <span className="text-gray-400">•</span>
          <span className="font-mono text-gray-500">
            {versionInfo.commitHash.substring(0, 7)}
          </span>
        </>
      )}
    </div>
  );
};

export default VersionDisplay;
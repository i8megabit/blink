import { useState, useEffect } from 'react';
import { AppSettings } from '../types';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { Button } from './ui/Button';
import { Input } from './ui/Input';
import { cn } from '../lib/utils';
import { 
  Settings as SettingsIcon, 
  Moon, 
  Sun, 
  Monitor,
  Bell,
  Volume2,
  RefreshCw,
  Save,
  Globe,
  Clock,
  Database,
  Zap
} from 'lucide-react';

interface SettingsProps {
  className?: string;
  onSettingsChange?: (settings: AppSettings) => void;
}

export function Settings({ 
  className,
  onSettingsChange
}: SettingsProps) {
  const [settings, setSettings] = useState<AppSettings>({
    theme: 'system',
    language: 'ru',
    autoRefresh: true,
    refreshInterval: 30,
    notifications: true,
    sound: false
  });
  const [loading, setLoading] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const response = await fetch('/api/v1/settings');
      if (response.ok) {
        const data = await response.json();
        setSettings(data.settings || settings);
      }
    } catch (err) {
      console.error('Ошибка загрузки настроек:', err);
    }
  };

  const saveSettings = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/settings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ settings }),
      });

      if (response.ok) {
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
        
        if (onSettingsChange) {
          onSettingsChange(settings);
        }
      } else {
        throw new Error('Не удалось сохранить настройки');
      }
    } catch (err) {
      console.error('Ошибка сохранения настроек:', err);
    } finally {
      setLoading(false);
    }
  };

  const updateSetting = <K extends keyof AppSettings>(
    key: K, 
    value: AppSettings[K]
  ) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  const themeOptions = [
    { value: 'light', label: 'Светлая', icon: <Sun className="w-4 h-4" /> },
    { value: 'dark', label: 'Темная', icon: <Moon className="w-4 h-4" /> },
    { value: 'system', label: 'Системная', icon: <Monitor className="w-4 h-4" /> }
  ];

  const languageOptions = [
    { value: 'ru', label: 'Русский' },
    { value: 'en', label: 'English' }
  ];

  return (
    <div className={cn("space-y-6", className)}>
      {/* Внешний вид */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Monitor className="w-5 h-5" />
            Внешний вид
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-2 block">Тема</label>
            <div className="grid grid-cols-3 gap-2">
              {themeOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => updateSetting('theme', option.value as AppSettings['theme'])}
                  className={cn(
                    "flex items-center gap-2 p-3 rounded-lg border transition-colors",
                    settings.theme === option.value
                      ? "bg-blue-50 border-blue-200 text-blue-700"
                      : "bg-white border-gray-200 hover:bg-gray-50"
                  )}
                >
                  {option.icon}
                  <span className="text-sm">{option.label}</span>
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block">Язык</label>
            <select
              value={settings.language}
              onChange={(e) => updateSetting('language', e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {languageOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Уведомления */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="w-5 h-5" />
            Уведомления
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Bell className="w-5 h-5 text-gray-500" />
              <div>
                <p className="font-medium">Включить уведомления</p>
                <p className="text-sm text-gray-500">Показывать уведомления о событиях</p>
              </div>
            </div>
            <button
              onClick={() => updateSetting('notifications', !settings.notifications)}
              className={cn(
                "w-12 h-6 rounded-full transition-colors",
                settings.notifications ? "bg-blue-500" : "bg-gray-300"
              )}
            >
              <div className={cn(
                "w-4 h-4 bg-white rounded-full transition-transform",
                settings.notifications ? "translate-x-6" : "translate-x-1"
              )} />
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Volume2 className="w-5 h-5 text-gray-500" />
              <div>
                <p className="font-medium">Звуковые уведомления</p>
                <p className="text-sm text-gray-500">Воспроизводить звук при уведомлениях</p>
              </div>
            </div>
            <button
              onClick={() => updateSetting('sound', !settings.sound)}
              className={cn(
                "w-12 h-6 rounded-full transition-colors",
                settings.sound ? "bg-blue-500" : "bg-gray-300"
              )}
            >
              <div className={cn(
                "w-4 h-4 bg-white rounded-full transition-transform",
                settings.sound ? "translate-x-6" : "translate-x-1"
              )} />
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Автообновление */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <RefreshCw className="w-5 h-5" />
            Автообновление
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <RefreshCw className="w-5 h-5 text-gray-500" />
              <div>
                <p className="font-medium">Автоматическое обновление</p>
                <p className="text-sm text-gray-500">Обновлять данные автоматически</p>
              </div>
            </div>
            <button
              onClick={() => updateSetting('autoRefresh', !settings.autoRefresh)}
              className={cn(
                "w-12 h-6 rounded-full transition-colors",
                settings.autoRefresh ? "bg-blue-500" : "bg-gray-300"
              )}
            >
              <div className={cn(
                "w-4 h-4 bg-white rounded-full transition-transform",
                settings.autoRefresh ? "translate-x-6" : "translate-x-1"
              )} />
            </button>
          </div>

          {settings.autoRefresh && (
            <div>
              <label className="text-sm font-medium mb-2 block">Интервал обновления (секунды)</label>
              <Input
                type="number"
                min="5"
                max="300"
                value={settings.refreshInterval}
                onChange={(e) => updateSetting('refreshInterval', parseInt(e.target.value) || 30)}
                className="w-32"
              />
            </div>
          )}
        </CardContent>
      </Card>

      {/* Системная информация */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="w-5 h-5" />
            Системная информация
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <Globe className="w-5 h-5 text-blue-500" />
              <div>
                <p className="text-sm font-medium">Версия API</p>
                <p className="text-xs text-gray-500">v1.0.0</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <Zap className="w-5 h-5 text-green-500" />
              <div>
                <p className="text-sm font-medium">Статус Ollama</p>
                <p className="text-xs text-gray-500">Подключено</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <Clock className="w-5 h-5 text-purple-500" />
              <div>
                <p className="text-sm font-medium">Время работы</p>
                <p className="text-xs text-gray-500">2ч 15м</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <Database className="w-5 h-5 text-orange-500" />
              <div>
                <p className="text-sm font-medium">База данных</p>
                <p className="text-xs text-gray-500">PostgreSQL</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Кнопки действий */}
      <div className="flex justify-end gap-3">
        <Button variant="outline" onClick={loadSettings}>
          Сбросить
        </Button>
        <Button 
          onClick={saveSettings} 
          disabled={loading}
          className="flex items-center gap-2"
        >
          {loading ? (
            <RefreshCw className="w-4 h-4 animate-spin" />
          ) : saved ? (
            <Save className="w-4 h-4" />
          ) : (
            <Save className="w-4 h-4" />
          )}
          {loading ? 'Сохранение...' : saved ? 'Сохранено!' : 'Сохранить'}
        </Button>
      </div>
    </div>
  );
} 
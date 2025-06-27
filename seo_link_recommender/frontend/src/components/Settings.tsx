import { useState, useEffect } from 'react';
import { AppSettings } from '../types';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { Button } from './ui/Button';
import { Input } from './ui/Input';
import { cn } from '../lib/utils';
import { 
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
  Zap,
  Check
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

  // Применяем тему при изменении настроек
  useEffect(() => {
    applyTheme(settings.theme);
  }, [settings.theme]);

  const loadSettings = async () => {
    try {
      const response = await fetch('/api/v1/settings');
      if (response.ok) {
        const data = await response.json();
        const loadedSettings = data.settings || settings;
        setSettings(loadedSettings);
        applyTheme(loadedSettings.theme);
      }
    } catch (err) {
      console.error('Ошибка загрузки настроек:', err);
    }
  };

  const applyTheme = (theme: string) => {
    const root = document.documentElement;
    
    // Удаляем все классы тем
    root.classList.remove('light', 'dark');
    
    if (theme === 'system') {
      // Определяем системную тему
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      root.classList.add(systemTheme);
    } else {
      root.classList.add(theme);
    }
    
    // Сохраняем в localStorage
    localStorage.setItem('theme', theme);
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
    { value: 'ru', label: 'Русский', flag: '🇷🇺' },
    { value: 'en', label: 'English', flag: '🇺🇸' }
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
        <CardContent className="space-y-6">
          <div>
            <label className="text-sm font-medium mb-3 block text-foreground">
              Тема оформления
            </label>
            <div className="grid grid-cols-3 gap-3">
              {themeOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => updateSetting('theme', option.value as AppSettings['theme'])}
                  className={cn(
                    "flex flex-col items-center gap-2 p-4 rounded-lg border transition-all duration-200",
                    "hover:shadow-md hover:scale-105",
                    settings.theme === option.value
                      ? "bg-primary/10 border-primary/30 text-primary shadow-md scale-105"
                      : "bg-card border-border hover:bg-accent hover:border-accent-foreground/20"
                  )}
                >
                  <div className={cn(
                    "p-2 rounded-full",
                    settings.theme === option.value 
                      ? "bg-primary/20" 
                      : "bg-muted"
                  )}>
                    {option.icon}
                  </div>
                  <span className="text-sm font-medium">{option.label}</span>
                  {settings.theme === option.value && (
                    <Check className="w-4 h-4 text-primary" />
                  )}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="text-sm font-medium mb-3 block text-foreground">
              Язык интерфейса
            </label>
            <div className="grid grid-cols-2 gap-3">
              {languageOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => updateSetting('language', option.value)}
                  className={cn(
                    "flex items-center gap-3 p-3 rounded-lg border transition-all duration-200",
                    "hover:shadow-md hover:scale-105",
                    settings.language === option.value
                      ? "bg-primary/10 border-primary/30 text-primary shadow-md scale-105"
                      : "bg-card border-border hover:bg-accent hover:border-accent-foreground/20"
                  )}
                >
                  <span className="text-lg">{option.flag}</span>
                  <span className="font-medium">{option.label}</span>
                  {settings.language === option.value && (
                    <Check className="w-4 h-4 text-primary ml-auto" />
                  )}
                </button>
              ))}
            </div>
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
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between p-4 rounded-lg bg-muted/50">
            <div className="flex items-center gap-3">
              <Bell className="w-5 h-5 text-muted-foreground" />
              <div>
                <p className="font-medium text-foreground">Включить уведомления</p>
                <p className="text-sm text-muted-foreground">Показывать уведомления о событиях</p>
              </div>
            </div>
            <button
              onClick={() => updateSetting('notifications', !settings.notifications)}
              className={cn(
                "relative w-12 h-6 rounded-full transition-all duration-200",
                settings.notifications ? "bg-primary" : "bg-muted-foreground/30"
              )}
            >
              <div className={cn(
                "absolute top-0.5 w-5 h-5 bg-white rounded-full transition-all duration-200 shadow-sm",
                settings.notifications ? "translate-x-6" : "translate-x-0.5"
              )} />
            </button>
          </div>

          <div className="flex items-center justify-between p-4 rounded-lg bg-muted/50">
            <div className="flex items-center gap-3">
              <Volume2 className="w-5 h-5 text-muted-foreground" />
              <div>
                <p className="font-medium text-foreground">Звуковые уведомления</p>
                <p className="text-sm text-muted-foreground">Воспроизводить звук при уведомлениях</p>
              </div>
            </div>
            <button
              onClick={() => updateSetting('sound', !settings.sound)}
              className={cn(
                "relative w-12 h-6 rounded-full transition-all duration-200",
                settings.sound ? "bg-primary" : "bg-muted-foreground/30"
              )}
            >
              <div className={cn(
                "absolute top-0.5 w-5 h-5 bg-white rounded-full transition-all duration-200 shadow-sm",
                settings.sound ? "translate-x-6" : "translate-x-0.5"
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
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between p-4 rounded-lg bg-muted/50">
            <div className="flex items-center gap-3">
              <Clock className="w-5 h-5 text-muted-foreground" />
              <div>
                <p className="font-medium text-foreground">Автоматическое обновление</p>
                <p className="text-sm text-muted-foreground">Обновлять данные автоматически</p>
              </div>
            </div>
            <button
              onClick={() => updateSetting('autoRefresh', !settings.autoRefresh)}
              className={cn(
                "relative w-12 h-6 rounded-full transition-all duration-200",
                settings.autoRefresh ? "bg-primary" : "bg-muted-foreground/30"
              )}
            >
              <div className={cn(
                "absolute top-0.5 w-5 h-5 bg-white rounded-full transition-all duration-200 shadow-sm",
                settings.autoRefresh ? "translate-x-6" : "translate-x-0.5"
              )} />
            </button>
          </div>

          {settings.autoRefresh && (
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">
                Интервал обновления (секунды)
              </label>
              <Input
                type="number"
                min="10"
                max="300"
                value={settings.refreshInterval}
                onChange={(e) => updateSetting('refreshInterval', parseInt(e.target.value) || 30)}
                className="w-full"
              />
              <p className="text-xs text-muted-foreground">
                Минимум 10 секунд, максимум 5 минут
              </p>
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

      {/* Кнопка сохранения */}
      <div className="flex justify-end">
        <Button
          onClick={saveSettings}
          disabled={loading}
          className="min-w-[120px]"
        >
          {loading ? (
            <>
              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              Сохранение...
            </>
          ) : saved ? (
            <>
              <Check className="w-4 h-4 mr-2" />
              Сохранено!
            </>
          ) : (
            <>
              <Save className="w-4 h-4 mr-2" />
              Сохранить
            </>
          )}
        </Button>
      </div>
    </div>
  );
} 
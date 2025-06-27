import React, { useState, useEffect, useRef } from 'react';

const AIAnalysisFlow = ({ isVisible, messages = [], onClose }) => {
  const [visibleMessages, setVisibleMessages] = useState([]);
  const messagesEndRef = useRef(null);
  const [isTyping, setIsTyping] = useState(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [visibleMessages]);

  useEffect(() => {
    if (!isVisible) {
      setVisibleMessages([]);
      return;
    }

    let currentIndex = 0;
    const addMessageWithDelay = () => {
      if (currentIndex < messages.length) {
        setIsTyping(true);
        
        setTimeout(() => {
          setVisibleMessages(prev => [...prev, messages[currentIndex]]);
          setIsTyping(false);
          currentIndex++;
          
          if (currentIndex < messages.length) {
            setTimeout(addMessageWithDelay, 800 + Math.random() * 400);
          }
        }, 500);
      }
    };

    if (messages.length > 0) {
      addMessageWithDelay();
    }
  }, [isVisible, messages]);

  if (!isVisible) return null;

  const getMessageIcon = (type) => {
    switch (type) {
      case 'ai_thinking':
        return '🧠';
      case 'enhanced_ai_thinking':
        return '🔬';
      case 'progress':
        return '⚡';
      case 'ollama':
        return '🤖';
      case 'error':
        return '❌';
      default:
        return '💭';
    }
  };

  const getMessageStyle = (type) => {
    switch (type) {
      case 'ai_thinking':
        return 'bg-gradient-to-r from-blue-50 to-indigo-50 border-l-4 border-blue-400';
      case 'enhanced_ai_thinking':
        return 'bg-gradient-to-r from-purple-50 to-pink-50 border-l-4 border-purple-400';
      case 'progress':
        return 'bg-gradient-to-r from-green-50 to-emerald-50 border-l-4 border-green-400';
      case 'ollama':
        return 'bg-gradient-to-r from-orange-50 to-amber-50 border-l-4 border-orange-400';
      case 'error':
        return 'bg-gradient-to-r from-red-50 to-pink-50 border-l-4 border-red-400';
      default:
        return 'bg-gradient-to-r from-gray-50 to-slate-50 border-l-4 border-gray-400';
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl h-[80vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 rounded-t-2xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-white bg-opacity-20 rounded-full flex items-center justify-center">
                <span className="text-xl">🧠</span>
              </div>
              <div>
                <h2 className="text-xl font-semibold">Анализ ИИ в реальном времени</h2>
                <p className="text-blue-100 text-sm">Отслеживание мыслей и процесса анализа</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="w-8 h-8 bg-white bg-opacity-20 rounded-full flex items-center justify-center hover:bg-opacity-30 transition-all"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Messages Container */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-gray-50">
          {visibleMessages.map((message, index) => (
            <div
              key={index}
              className={`${getMessageStyle(message.type)} rounded-lg p-4 shadow-sm transform transition-all duration-500 animate-slide-in`}
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="flex items-start space-x-3">
                <div className="text-2xl">{getMessageIcon(message.type)}</div>
                <div className="flex-1">
                  {message.type === 'ai_thinking' && (
                    <div className="space-y-2">
                      <div className="text-sm text-gray-600 font-medium">
                        Мысль ИИ • {message.thinking_stage}
                      </div>
                      <div className="text-gray-800 leading-relaxed">
                        {message.thought}
                      </div>
                    </div>
                  )}
                  
                  {message.type === 'enhanced_ai_thinking' && (
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="text-sm text-gray-600 font-medium">
                          Расширенный анализ • {message.stage}
                        </div>
                        <div className="text-xs text-gray-500">
                          Уверенность: {Math.round(message.confidence * 100)}%
                        </div>
                      </div>
                      <div className="text-gray-800 leading-relaxed">
                        {message.content}
                      </div>
                      {message.related_concepts && message.related_concepts.length > 0 && (
                        <div className="flex flex-wrap gap-2 mt-2">
                          {message.related_concepts.slice(0, 5).map((concept, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full"
                            >
                              {concept}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                  
                  {message.type === 'progress' && (
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="text-sm text-gray-600 font-medium">
                          {message.step}
                        </div>
                        <div className="text-xs text-gray-500">
                          {message.current}/{message.total} ({message.percentage}%)
                        </div>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-gradient-to-r from-green-400 to-blue-500 h-2 rounded-full transition-all duration-500"
                          style={{ width: `${message.percentage}%` }}
                        />
                      </div>
                      {message.details && (
                        <div className="text-gray-700 text-sm mt-1">
                          {message.details}
                        </div>
                      )}
                    </div>
                  )}
                  
                  {message.type === 'ollama' && (
                    <div className="space-y-2">
                      <div className="text-sm text-gray-600 font-medium">
                        🤖 Ollama • {message.info?.status || 'Обработка'}
                      </div>
                      <div className="text-gray-800 text-sm">
                        {message.info?.message || JSON.stringify(message.info)}
                      </div>
                    </div>
                  )}
                  
                  {message.type === 'error' && (
                    <div className="space-y-2">
                      <div className="text-sm text-red-600 font-medium">
                        Ошибка
                      </div>
                      <div className="text-red-700">
                        {message.message}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
          
          {/* Typing Indicator */}
          {isTyping && (
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-l-4 border-blue-400 rounded-lg p-4 shadow-sm">
              <div className="flex items-center space-x-3">
                <div className="text-2xl">💭</div>
                <div className="flex items-center space-x-1">
                  <div className="text-gray-600">ИИ думает</div>
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Footer */}
        <div className="bg-gray-100 p-4 rounded-b-2xl">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
              <span>WebSocket подключен</span>
            </div>
            <div>
              Сообщений: {visibleMessages.length}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIAnalysisFlow; 
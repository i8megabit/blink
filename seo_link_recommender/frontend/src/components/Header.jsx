import React from 'react'

function Header() {
  return (
    <header className="text-center py-8 text-white">
      <div className="max-w-6xl mx-auto px-4">
        <h1 className="text-4xl md:text-5xl font-bold mb-4 gradient-text text-shadow-lg">
          🔗 SEO Link Recommender
        </h1>
        <p className="text-lg md:text-xl text-white/90 max-w-2xl mx-auto">
          Современный анализ внутренних ссылок WordPress сайтов с помощью ИИ Ollama и Qwen2.5
        </p>
        <div className="mt-4 flex justify-center gap-4 text-sm text-white/70">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
            Vite Edition
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></span>
            Tailwind CSS
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 bg-purple-400 rounded-full animate-pulse"></span>
            Fast HMR
          </span>
        </div>
      </div>
    </header>
  )
}

export default Header 
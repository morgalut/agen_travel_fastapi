'use client';

import { useState, useRef, useEffect } from 'react';
// Using simple SVG icons instead of lucide-react to avoid import issues
const SendIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
  </svg>
);

const PlaneIcon = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
  </svg>
);

const MapPinIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
);

const SuitcaseIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
  </svg>
);

const CameraIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
);

const LoaderIcon = () => (
  <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
  </svg>
);
import { sendMessage, ChatMessage } from '@/lib/api';

export default function Home() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isClient, setIsClient] = useState(false);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showQuickQuestions, setShowQuickQuestions] = useState(true);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [isListening, setIsListening] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const recognitionRef = useRef<any>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Initialize client-side state and welcome message
  useEffect(() => {
    setIsClient(true);
    if (messages.length === 0) {
      setMessages([{
        id: '1',
        text: "Welcome to WanderGuide! ✈️\n\nI'm your personal travel companion, ready to help you plan your next adventure. Whether you need packing tips, destination recommendations, or local insights, I'm here to make your travel planning effortless.\n\n**What can I help you with today?**\n• Destination recommendations\n• Packing lists and travel tips\n• Local attractions and hidden gems\n• Weather and seasonal advice\n• Budget planning and cost estimates\n\nJust ask me anything about travel!",
        isUser: false,
        timestamp: new Date(),
      }]);
    }
  }, []);

  // Initialize speech recognition
  useEffect(() => {
    if (typeof window !== 'undefined' && 'webkitSpeechRecognition' in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setInputText(transcript);
        setIsListening(false);
        playSound('notification');
      };

      recognitionRef.current.onerror = () => {
        setIsListening(false);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };

      setIsSupported(true);
    }
  }, []);

  // Play sound effect
  const playSound = (type: 'send' | 'receive' | 'notification') => {
    if (!soundEnabled) return;
    
    // Create audio context for sound effects
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    // Different frequencies for different sounds
    const frequencies = {
      send: 800,
      receive: 600,
      notification: 1000
    };
    
    oscillator.frequency.setValueAtTime(frequencies[type], audioContext.currentTime);
    oscillator.type = 'sine';
    
    gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);
    
    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.2);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      text: inputText.trim(),
      isUser: true,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setShowQuickQuestions(false);
    setIsLoading(true);
    playSound('send');

    try {
      const response = await sendMessage(inputText.trim());

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        text: response.answer,  // use answer not response
        isUser: false,
        timestamp: new Date(),
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      playSound('receive');
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        text: error instanceof Error ? error.message : 'Sorry, I encountered an error. Please try again.',
        isUser: false,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const quickQuestions = [
    { text: "What should I pack for a 5-day trip to Paris in winter?", icon: SuitcaseIcon, category: "Packing" },
    { text: "What attractions should I see while in Paris?", icon: CameraIcon, category: "Attractions" },
    { text: "Recommend a destination for a romantic getaway", icon: MapPinIcon, category: "Destinations" },
    { text: "What's the weather like in Tokyo in spring?", icon: MapPinIcon, category: "Weather" },
    { text: "How much should I budget for a week in Europe?", icon: SuitcaseIcon, category: "Budget" },
    { text: "Best time to visit Bali for surfing?", icon: MapPinIcon, category: "Seasons" },
    { text: "Solo travel safety tips for women", icon: SuitcaseIcon, category: "Safety" },
    { text: "Hidden gems in Barcelona", icon: CameraIcon, category: "Local Tips" },
    { text: "Visa requirements for Thailand", icon: SuitcaseIcon, category: "Documents" },
  ];

  const handleQuickQuestion = (question: string) => {
    setInputText(question);
    setShowQuickQuestions(false);
  };

  const clearConversation = () => {
    setMessages([{
      id: '1',
      text: "Welcome to WanderGuide! ✈️\n\nI'm your personal travel companion, ready to help you plan your next adventure. Whether you need packing tips, destination recommendations, or local insights, I'm here to make your travel planning effortless.\n\n**What can I help you with today?**\n• Destination recommendations\n• Packing lists and travel tips\n• Local attractions and hidden gems\n• Weather and seasonal advice\n• Budget planning and cost estimates\n\nJust ask me anything about travel!",
      isUser: false,
      timestamp: new Date(),
    }]);
    setShowQuickQuestions(true);
    playSound('notification');
  };

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
    playSound('notification');
  };

  const toggleSound = () => {
    setSoundEnabled(!soundEnabled);
    playSound('notification');
  };

  const addReaction = (messageId: string, reaction: string) => {
    // In a real app, you'd update the message with reactions
    console.log(`Added ${reaction} reaction to message ${messageId}`);
    playSound('notification');
  };

  const startListening = () => {
    if (recognitionRef.current && !isListening) {
      setIsListening(true);
      recognitionRef.current.start();
      playSound('notification');
    }
  };

  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    }
  };

  const exportChat = () => {
    const chatText = messages.map(msg => 
      `${msg.isUser ? 'You' : 'WanderGuide'}: ${msg.text}\n${msg.timestamp.toLocaleString()}\n`
    ).join('\n');
    
    const blob = new Blob([chatText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `wanderGuide-chat-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    playSound('notification');
  };

  // Prevent hydration mismatch by not rendering until client-side
  if (!isClient) {
    return (
      <div className="min-h-screen relative overflow-hidden bg-gradient-to-br from-wanderlust-50 via-ocean-50 to-forest-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-ocean-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-wanderlust-600 font-medium">Loading WanderGuide...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen relative overflow-hidden transition-colors duration-500 ${isDarkMode ? 'dark' : ''}`}>
      {/* Background Elements */}
      <div className="absolute inset-0 bg-travel-pattern opacity-30"></div>
      <div className={`absolute top-0 right-0 w-96 h-96 rounded-full blur-3xl floating-element ${isDarkMode ? 'bg-gradient-to-br from-ocean-400/20 to-sunset-400/20' : 'bg-gradient-to-br from-ocean-200/20 to-sunset-200/20'}`}></div>
      <div className={`absolute bottom-0 left-0 w-80 h-80 rounded-full blur-3xl floating-element ${isDarkMode ? 'bg-gradient-to-tr from-forest-400/20 to-ocean-400/20' : 'bg-gradient-to-tr from-forest-200/20 to-ocean-200/20'}`} style={{animationDelay: '3s'}}></div>
      
      {/* Header */}
      <div className="relative z-10">
        <div className="glass-card mx-2 sm:mx-4 mt-4 sm:mt-6 rounded-2xl shadow-2xl border border-white/30">
          <div className="px-4 sm:px-6 lg:px-8 py-4 sm:py-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3 sm:space-x-4">
                <div className="relative">
                  <div className="p-2 sm:p-3 bg-gradient-to-br from-ocean-500 to-ocean-600 rounded-xl sm:rounded-2xl shadow-lg">
                    <PlaneIcon />
                  </div>
                  <div className="absolute -top-0.5 -right-0.5 sm:-top-1 sm:-right-1 w-2 h-2 sm:w-3 sm:h-3 bg-sunset-400 rounded-full animate-pulse"></div>
                </div>
                <div>
                  <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold gradient-text">WanderGuide</h1>
                  <p className="text-xs sm:text-sm text-wanderlust-600 font-medium">Your personal travel companion</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <div className="flex items-center space-x-2 text-xs sm:text-sm text-wanderlust-500">
                  <div className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-forest-400 rounded-full animate-pulse"></div>
                  <span className="hidden sm:inline">Online</span>
                  <span className="sm:hidden">●</span>
                </div>
                
                {/* Control Buttons */}
                <div className="flex items-center space-x-2">
                  <button
                    onClick={toggleSound}
                    className={`p-2 rounded-lg transition-all duration-200 ${soundEnabled ? 'text-ocean-600 bg-ocean-100' : 'text-wanderlust-400 bg-wanderlust-100'}`}
                    title={soundEnabled ? 'Disable sounds' : 'Enable sounds'}
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      {soundEnabled ? (
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                      ) : (
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15zM17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
                      )}
                    </svg>
                  </button>
                  
                  <button
                    onClick={toggleDarkMode}
                    className="p-2 rounded-lg transition-all duration-200 text-wanderlust-500 hover:text-ocean-600 bg-wanderlust-100 hover:bg-ocean-100"
                    title={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      {isDarkMode ? (
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                      ) : (
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                      )}
                    </svg>
                  </button>
                  
                  <button
                    onClick={exportChat}
                    className="p-2 rounded-lg transition-all duration-200 text-wanderlust-500 hover:text-ocean-600 bg-wanderlust-100 hover:bg-ocean-100"
                    title="Export conversation"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </button>
                  
                  {messages.length > 1 && (
                    <button
                      onClick={clearConversation}
                      className="px-3 py-1.5 text-xs font-medium text-wanderlust-500 hover:text-ocean-600 bg-wanderlust-100 hover:bg-ocean-100 rounded-lg transition-all duration-200"
                    >
                      New Chat
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="relative z-10 max-w-5xl mx-auto px-2 sm:px-4 py-4 sm:py-6">
        <div className="glass-card rounded-2xl sm:rounded-3xl shadow-2xl border border-white/30 overflow-hidden">
          {/* Chat Messages */}
          <div className="h-[400px] sm:h-[500px] overflow-y-auto p-4 sm:p-6 lg:p-8 space-y-4 sm:space-y-6 bg-gradient-to-b from-white/50 to-wanderlust-50/30">
            {messages.map((message, index) => (
              <div
                key={message.id}
                className={`flex ${message.isUser ? 'justify-end' : 'justify-start'} animate-fade-in`}
                style={{animationDelay: `${index * 0.1}s`}}
              >
                <div
                  className={`chat-bubble ${
                    message.isUser ? 'user-bubble' : 'assistant-bubble'
                  } shimmer-effect max-w-[85%] sm:max-w-xs lg:max-w-lg message-enter`}
                >
<div className="text-sm leading-relaxed whitespace-pre-line">
  {(message.text ?? "").split("\n").map((line, lineIndex) => {
    if (line.startsWith("**") && line.endsWith("**")) {
      return (
        <div key={lineIndex} className="font-bold text-ocean-600 mt-3 mb-2 text-base">
          {line.slice(2, -2)}
        </div>
      );
    }
    if (line.startsWith("•")) {
      return (
        <div key={lineIndex} className="flex items-start ml-3 mb-2">
          <span className="text-sunset-500 mr-3 text-lg">•</span>
          <span className="text-wanderlust-700">{line.slice(1).trim()}</span>
        </div>
      );
    }
    return <div key={lineIndex} className="text-wanderlust-700">{line}</div>;
  })}
</div>

                  <div className="flex items-center justify-between mt-3">
                    <p className="text-xs text-wanderlust-400 font-medium">
                      {isClient ? message.timestamp.toLocaleTimeString() : 'Loading...'}
                    </p>
                    {!message.isUser && (
                      <div className="flex items-center space-x-1">
                        <div className="w-1.5 h-1.5 bg-forest-400 rounded-full"></div>
                        <span className="text-xs text-forest-500 font-medium">WanderGuide</span>
                      </div>
                    )}
                  </div>
                  
                  {/* Message Reactions */}
                  {!message.isUser && (
                    <div className="flex items-center space-x-2 mt-3 pt-2 border-t border-wanderlust-200/30">
                      <span className="text-xs text-wanderlust-400">React:</span>
                      <div className="flex items-center space-x-1">
                        {['👍', '❤️', '😊', '🤔', '✨'].map((emoji) => (
                          <button
                            key={emoji}
                            onClick={() => addReaction(message.id, emoji)}
                            className="p-1 hover:bg-wanderlust-100 rounded-full transition-all duration-200 text-sm hover:scale-110"
                            title={`Add ${emoji} reaction`}
                          >
                            {emoji}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="flex justify-start animate-slide-in-left">
                <div className="chat-bubble assistant-bubble">
                  <div className="flex items-center space-x-3">
                    <div className="typing-indicator">
                      <div className="typing-dot"></div>
                      <div className="typing-dot"></div>
                      <div className="typing-dot"></div>
                    </div>
                    <span className="text-sm text-wanderlust-500 font-medium">WanderGuide is thinking...</span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Questions */}
          {showQuickQuestions && (
            <div className="px-4 sm:px-6 lg:px-8 py-6 sm:py-8 bg-gradient-to-br from-wanderlust-50/50 to-ocean-50/30 border-t border-wanderlust-200/30">
              <div className="text-center mb-4 sm:mb-6">
                <h3 className="text-lg sm:text-xl lg:text-2xl font-bold gradient-text mb-2">Where to next?</h3>
                <p className="text-sm sm:text-base text-wanderlust-600 font-medium">Choose a topic to get started</p>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
                {quickQuestions.map((question, index) => {
                  const Icon = question.icon;
                  return (
                    <button
                      key={index}
                      onClick={() => handleQuickQuestion(question.text)}
                      className="group relative overflow-hidden bg-white/60 backdrop-blur-sm border border-wanderlust-200/50 rounded-xl sm:rounded-2xl p-4 sm:p-6 hover:bg-white/80 hover:border-ocean-300/50 hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 active:scale-95"
                      style={{animationDelay: `${index * 0.1}s`}}
                    >
                      <div className="absolute inset-0 bg-gradient-to-br from-ocean-500/5 to-sunset-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                      <div className="relative">
                        <div className="flex items-start space-x-3 sm:space-x-4">
                          <div className="flex-shrink-0 p-2 sm:p-3 bg-gradient-to-br from-ocean-100 to-ocean-200 rounded-lg sm:rounded-xl group-hover:from-ocean-200 group-hover:to-ocean-300 transition-all duration-300">
                            <Icon />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="text-xs font-bold text-ocean-600 mb-1 sm:mb-2 uppercase tracking-wide">{question.category}</div>
                            <div className="text-xs sm:text-sm text-wanderlust-700 group-hover:text-wanderlust-900 font-medium leading-relaxed">{question.text}</div>
                          </div>
                        </div>
                        <div className="mt-3 sm:mt-4 flex items-center text-xs text-wanderlust-400 group-hover:text-ocean-500 transition-colors">
                          <span className="hidden sm:inline">Tap to explore</span>
                          <span className="sm:hidden">Tap</span>
                          <div className="ml-2 w-3 h-3 sm:w-4 sm:h-4 rounded-full bg-gradient-to-r from-ocean-400 to-sunset-400 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Input Form */}
          <div className="px-4 sm:px-6 lg:px-8 py-4 sm:py-6 bg-gradient-to-r from-white/80 to-wanderlust-50/50 border-t border-wanderlust-200/30 backdrop-blur-sm">
            <form onSubmit={handleSubmit} className="relative">
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center space-y-3 sm:space-y-0 sm:space-x-4">
                <div className="flex-1 relative">
                  <input
                    type="text"
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    placeholder="Ask WanderGuide anything about your next adventure..."
                    className="w-full px-4 sm:px-6 py-3 sm:py-4 bg-white/80 backdrop-blur-sm border border-wanderlust-200/50 rounded-xl sm:rounded-2xl focus:outline-none focus:ring-2 focus:ring-ocean-400/50 focus:border-ocean-300 text-wanderlust-700 placeholder-wanderlust-400 font-medium shadow-lg transition-all duration-300 text-sm sm:text-base"
                    disabled={isLoading}
                  />
                  <div className="absolute right-3 sm:right-4 top-1/2 transform -translate-y-1/2 flex items-center space-x-2">
                    {isSupported && (
                      <button
                        onClick={isListening ? stopListening : startListening}
                        className={`p-1.5 rounded-full transition-all duration-200 ${
                          isListening 
                            ? 'text-red-500 bg-red-100 animate-pulse' 
                            : 'text-ocean-500 hover:text-ocean-600 hover:bg-ocean-100'
                        }`}
                        title={isListening ? 'Stop listening' : 'Start voice input'}
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                        </svg>
                      </button>
                    )}
                    <div className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-forest-400 rounded-full animate-pulse"></div>
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={!inputText.trim() || isLoading}
                  className="group relative px-6 sm:px-8 py-3 sm:py-4 bg-gradient-to-r from-ocean-500 to-ocean-600 text-white rounded-xl sm:rounded-2xl hover:from-ocean-600 hover:to-ocean-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-105 hover:shadow-xl disabled:hover:scale-100 active:scale-95 flex items-center justify-center space-x-2 font-semibold text-sm sm:text-base"
                >
                  {isLoading ? (
                    <>
                      <LoaderIcon />
                      <span className="hidden sm:inline">Thinking...</span>
                      <span className="sm:hidden">...</span>
                    </>
                  ) : (
                    <>
                      <SendIcon />
                      <span className="hidden sm:inline">Send</span>
                    </>
                  )}
                  <div className="absolute inset-0 bg-gradient-to-r from-white/20 to-transparent rounded-xl sm:rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>

      {/* Floating Action Button */}
      {!showQuickQuestions && (
        <div className="fixed bottom-6 right-6 z-20">
          <button
            onClick={() => setShowQuickQuestions(true)}
            className="group relative p-4 bg-gradient-to-r from-ocean-500 to-ocean-600 text-white rounded-full shadow-2xl hover:from-ocean-600 hover:to-ocean-700 transition-all duration-300 transform hover:scale-110 active:scale-95 pulse-glow bounce-in"
          >
            <div className="w-6 h-6 flex items-center justify-center">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
            </div>
            <div className="absolute inset-0 bg-gradient-to-r from-white/20 to-transparent rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            <div className="absolute -top-2 -right-2 w-3 h-3 bg-sunset-400 rounded-full animate-pulse"></div>
          </button>
        </div>
      )}
    </div>
  );
}

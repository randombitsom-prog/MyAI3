"use client";

import { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send, Bot, User } from 'lucide-react';
import { useChat } from 'ai/react';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

const WELCOME_MESSAGE: Message = {
  id: 'welcome-1',
  text: "Hi! I'm PlaceBot. I can help you with previous year interview transcripts, preparation tips, company insights, and more. How can I assist you today?",
  sender: 'bot',
  timestamp: new Date(),
};

export default function ChatBot() {
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const { messages: aiMessages, input: aiInput, handleInputChange: handleAIInputChange, handleSubmit: handleAISubmit, isLoading } = useChat({
    api: '/api/chat',
  });
  
  const [localMessages, setLocalMessages] = useState<Message[]>([WELCOME_MESSAGE]);
  const [input, setInput] = useState('');

  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }
    }
  }, [localMessages]);

  // Convert AI SDK messages to local format
  useEffect(() => {
    const newLocalMessages: Message[] = [WELCOME_MESSAGE];
    
    aiMessages.forEach((msg) => {
      let text = '';
      if (msg.parts) {
        msg.parts.forEach((part: { type?: string; text?: string }) => {
          if (part.type === 'text' && part.text) {
            text += part.text;
          }
        });
      }
      
      if (text) {
        newLocalMessages.push({
          id: msg.id || `msg-${Date.now()}-${Math.random()}`,
          text: text,
          sender: msg.role === 'user' ? 'user' : 'bot',
          timestamp: new Date(),
        });
      }
    });
    
    setLocalMessages(newLocalMessages);
  }, [aiMessages]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value);
    handleAIInputChange(e);
  };

  const handleQuickAction = (action: string) => {
    setInput(action);
    // Set the input value in the AI SDK
    handleAIInputChange({ target: { value: action } } as React.ChangeEvent<HTMLInputElement>);
    
    // Submit after a brief delay to ensure input is set
    setTimeout(() => {
      const syntheticEvent = {
        preventDefault: () => {},
      } as React.FormEvent<HTMLFormElement>;
      handleAISubmit(syntheticEvent);
    }, 10);
  };

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      handleAISubmit(e);
      setInput('');
    }
  };

  return (
    <Card className="h-[calc(100vh-120px)] flex flex-col sticky top-4 bg-gradient-to-br from-slate-800 to-slate-900 border-slate-700/50 shadow-xl">
      <CardHeader className="border-b border-slate-700/50 bg-gradient-to-r from-orange-600 to-orange-700">
        <CardTitle className="flex items-center gap-3 text-white">
          <div className="p-2 bg-white/20 rounded-lg backdrop-blur-sm">
            <Bot className="h-5 w-5 text-white" />
          </div>
          <div>
            <div>PlaceBot Assistant</div>
            <p className="text-xs text-orange-100 font-normal mt-0.5">
              Always here to help you
            </p>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col p-0">
        <ScrollArea className="flex-1 p-4 bg-slate-950/50" ref={scrollAreaRef}>
          <div className="space-y-4">
            {localMessages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-3 ${
                  message.sender === 'user' ? 'justify-end' : 'justify-start'
                } animate-in fade-in slide-in-from-bottom-2 duration-300`}
              >
                {message.sender === 'bot' && (
                  <div className="flex-shrink-0 w-9 h-9 rounded-xl bg-gradient-to-br from-orange-500 to-orange-600 flex items-center justify-center shadow-lg shadow-orange-500/30">
                    <Bot className="h-5 w-5 text-white" />
                  </div>
                )}
                <div
                  className={`max-w-[75%] rounded-2xl p-4 ${
                    message.sender === 'user'
                      ? 'bg-gradient-to-br from-blue-600 to-blue-700 text-white shadow-lg shadow-blue-500/20'
                      : 'bg-slate-800/80 text-slate-100 border border-slate-700/50 shadow-lg'
                  }`}
                >
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">
                    {message.text}
                  </p>
                  {message.text && (
                    <p className="text-xs mt-2 opacity-60">
                      {message.timestamp.toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </p>
                  )}
                </div>
                {message.sender === 'user' && (
                  <div className="flex-shrink-0 w-9 h-9 rounded-xl bg-gradient-to-br from-slate-600 to-slate-700 flex items-center justify-center shadow-lg">
                    <User className="h-5 w-5 text-slate-200" />
                  </div>
                )}
              </div>
            ))}
            {isLoading && (
              <div className="flex gap-3 justify-start">
                <div className="flex-shrink-0 w-9 h-9 rounded-xl bg-gradient-to-br from-orange-500 to-orange-600 flex items-center justify-center shadow-lg shadow-orange-500/30">
                  <Bot className="h-5 w-5 text-white" />
                </div>
                <div className="bg-slate-800/80 text-slate-100 border border-slate-700/50 shadow-lg rounded-2xl p-4">
                  <p className="text-sm text-slate-300">Fetching latest data...</p>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>
        <div className="p-4 border-t border-slate-700/50 bg-slate-900/50">
          <form onSubmit={onSubmit} className="flex gap-2 mb-3">
            <Input
              placeholder="Type your question here..."
              value={aiInput}
              onChange={handleInputChange}
              className="bg-slate-800/50 border-slate-700 text-white placeholder:text-slate-500 focus:border-orange-500 focus:ring-orange-500 h-11 rounded-xl"
              disabled={isLoading}
            />
            <Button 
              type="submit"
              disabled={isLoading || !aiInput.trim()}
              className="bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 h-11 w-11 rounded-xl shadow-lg shadow-orange-500/30"
            >
              <Send className="h-4 w-4" />
            </Button>
          </form>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleQuickAction("Show McKinsey interview transcript")}
              className="bg-slate-800/50 border-slate-700 text-slate-300 hover:bg-slate-700 hover:text-white hover:border-orange-500/50 rounded-lg text-xs"
              disabled={isLoading}
            >
              McKinsey Interview
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleQuickAction("Consulting preparation tips")}
              className="bg-slate-800/50 border-slate-700 text-slate-300 hover:bg-slate-700 hover:text-white hover:border-orange-500/50 rounded-lg text-xs"
              disabled={isLoading}
            >
              Prep Tips
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleQuickAction("Tell me about CTC stats")}
              className="bg-slate-800/50 border-slate-700 text-slate-300 hover:bg-slate-700 hover:text-white hover:border-orange-500/50 rounded-lg text-xs"
              disabled={isLoading}
            >
              CTC Info
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

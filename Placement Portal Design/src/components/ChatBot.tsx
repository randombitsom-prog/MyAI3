import { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { ScrollArea } from './ui/scroll-area';
import { Send, Bot, User } from 'lucide-react';

interface Message {
  id: number;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

export default function ChatBot() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      text: "Hi! I'm PlaceBot. I can help you with previous year interview transcripts, preparation tips, company insights, and more. How can I assist you today?",
      sender: 'bot',
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  const generateBotResponse = (userMessage: string): string => {
    const lowerMessage = userMessage.toLowerCase();

    // Interview transcript queries
    if (lowerMessage.includes('interview') || lowerMessage.includes('transcript')) {
      if (lowerMessage.includes('mckinsey')) {
        return "McKinsey interview transcripts from last year typically include case studies on market sizing, profitability analysis, and organizational restructuring. Students reported 2-3 rounds including a personal experience interview. Would you like specific details about any round?";
      }
      if (lowerMessage.includes('jpmc') || lowerMessage.includes('jp morgan')) {
        return "JPMC interviews focused on technical questions about financial markets, portfolio management, and behavioral questions. The process included an online assessment followed by 2 technical rounds. Need more details?";
      }
      if (lowerMessage.includes('accenture')) {
        return "Accenture interviews included aptitude tests, technical discussions about digital transformation, and HR rounds. Students suggested preparing on cloud technologies and agile methodologies.";
      }
      return "I have interview transcripts for companies like McKinsey, JPMC, Accenture, KPMG, EY, and more. Which company are you interested in?";
    }

    // Preparation tips
    if (lowerMessage.includes('prepare') || lowerMessage.includes('preparation') || lowerMessage.includes('tips')) {
      if (lowerMessage.includes('consulting')) {
        return "For consulting roles: Practice case studies daily, read business newspapers, improve your mental math, and practice frameworks like Porter's Five Forces, BCG Matrix, and 4Ps of Marketing.";
      }
      if (lowerMessage.includes('finance')) {
        return "For finance roles: Brush up on financial modeling, valuation techniques, market analysis. Practice Excel shortcuts and stay updated with current market trends. CFA Level 1 preparation materials can be helpful.";
      }
      return "Start with: 1) Resume building and mock interviews 2) Company-specific preparation 3) Technical skill enhancement 4) Case study practice 5) Networking with alumni. What specific area would you like help with?";
    }

    // CTC queries
    if (lowerMessage.includes('ctc') || lowerMessage.includes('salary') || lowerMessage.includes('package')) {
      return "This year's placement stats: Highest CTC is 40 LPA, Average CTC is 25 LPA, and Lowest CTC is 15.5 LPA. Top paying companies include McKinsey, JPMC, and BoFA. Would you like company-specific CTC information?";
    }

    // Company-specific queries
    if (lowerMessage.includes('abg') || lowerMessage.includes('aditya birla')) {
      return "ABG offered the most positions this year with 17 offers. They recruit for roles across FMCG, Finance, and Operations. The selection process includes group discussions and multiple interview rounds.";
    }

    if (lowerMessage.includes('kpmg')) {
      return "KPMG offered 7 positions this year. They focus on consulting and audit roles. Interview process includes case studies and technical assessments. Average CTC ranges from 18-22 LPA.";
    }

    // General stats
    if (lowerMessage.includes('stats') || lowerMessage.includes('statistics') || lowerMessage.includes('placement')) {
      return "Key stats: 75 students placed (41 PPOs, 31 Campus, 3 Off-campus), 82 still unplaced. Top recruiters include ABG (17), KPMG (7), Saint Gobain (5), and Freyr (5). What specific information do you need?";
    }

    // Default responses
    const responses = [
      "That's an interesting question! Could you be more specific? I can help with interview transcripts, preparation strategies, CTC information, or company-specific insights.",
      "I'm here to help with placement-related queries. You can ask me about previous interviews, preparation tips, company information, or placement statistics.",
      "I can assist you with: Interview experiences, Preparation resources, Company insights, CTC details, or Placement statistics. What would you like to know?",
    ];
    return responses[Math.floor(Math.random() * responses.length)];
  };

  const handleSendMessage = () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: messages.length + 1,
      text: inputValue,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');

    // Simulate bot response with a delay
    setTimeout(() => {
      const botResponse: Message = {
        id: messages.length + 2,
        text: generateBotResponse(inputValue),
        sender: 'bot',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, botResponse]);
    }, 1000);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSendMessage();
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
            {messages.map((message) => (
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
                  <p className="text-sm leading-relaxed">{message.text}</p>
                  <p className="text-xs mt-2 opacity-60">
                    {message.timestamp.toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                </div>
                {message.sender === 'user' && (
                  <div className="flex-shrink-0 w-9 h-9 rounded-xl bg-gradient-to-br from-slate-600 to-slate-700 flex items-center justify-center shadow-lg">
                    <User className="h-5 w-5 text-slate-200" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </ScrollArea>
        <div className="p-4 border-t border-slate-700/50 bg-slate-900/50">
          <div className="flex gap-2 mb-3">
            <Input
              placeholder="Type your question here..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              className="bg-slate-800/50 border-slate-700 text-white placeholder:text-slate-500 focus:border-orange-500 focus:ring-orange-500 h-11 rounded-xl"
            />
            <Button 
              onClick={handleSendMessage} 
              className="bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 h-11 w-11 rounded-xl shadow-lg shadow-orange-500/30"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setInputValue("Show McKinsey interview transcript")}
              className="bg-slate-800/50 border-slate-700 text-slate-300 hover:bg-slate-700 hover:text-white hover:border-orange-500/50 rounded-lg text-xs"
            >
              McKinsey Interview
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setInputValue("Consulting preparation tips")}
              className="bg-slate-800/50 border-slate-700 text-slate-300 hover:bg-slate-700 hover:text-white hover:border-orange-500/50 rounded-lg text-xs"
            >
              Prep Tips
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setInputValue("Tell me about CTC stats")}
              className="bg-slate-800/50 border-slate-700 text-slate-300 hover:bg-slate-700 hover:text-white hover:border-orange-500/50 rounded-lg text-xs"
            >
              CTC Info
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
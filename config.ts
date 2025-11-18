import { openai } from "@ai-sdk/openai";
import { wrapLanguageModel, extractReasoningMiddleware } from "ai";

export const MODEL = openai('gpt-5-mini');

function getDateAndTime(): string {
    const now = new Date();
    const dateStr = now.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
    const timeStr = now.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        timeZoneName: 'short'
    });
    return `The day today is ${dateStr} and the time right now is ${timeStr}.`;
}

export const DATE_AND_TIME = getDateAndTime();

export const AI_NAME = "Bit";
export const OWNER_NAME = "Prof. Daniel Ringel";

export const WELCOME_MESSAGE = `Hello! I'm ${AI_NAME}, an AI assistant created by ${OWNER_NAME}. I'm here to help you with questions about the course. Feel free to ask me anything!`;

export const CLEAR_CHAT_TEXT = "New";

export const MODERATION_DENIAL_MESSAGE = "Your message violates our guidelines, I can not answer that";

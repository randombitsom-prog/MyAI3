import OpenAI from 'openai';


export async function isContentFlagged(text: string): Promise<boolean> {
    if (!text || text.trim().length === 0) {
        return false;
    }

    const openai = new OpenAI({
        apiKey: process.env.OPENAI_API_KEY,
    });

    try {
        const moderationResult = await openai.moderations.create({
            input: text,
        });

        return moderationResult.results[0]?.flagged ?? false;
    } catch (error) {
        return false;
    }
}


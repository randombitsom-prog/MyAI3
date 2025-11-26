import { Pinecone } from '@pinecone-database/pinecone';
import { PINECONE_TOP_K } from '@/config';
import { searchResultsToChunks, getSourcesFromChunks, getContextFromSources } from '@/lib/sources';
import { PINECONE_INDEX_NAME } from '@/config';

if (!process.env.PINECONE_API_KEY) {
    throw new Error('PINECONE_API_KEY is not set');
}

export const pinecone = new Pinecone({
    apiKey: process.env.PINECONE_API_KEY,
});

export const pineconeIndex = pinecone.Index(PINECONE_INDEX_NAME);

export async function searchPinecone(
    query: string,
): Promise<{ context: string; companies: string[] }> {
    const results = await pineconeIndex.namespace('placements').searchRecords({
        query: {
            inputs: {
                text: query,
            },
            topK: PINECONE_TOP_K,
        },
        fields: ['text', 'pre_context', 'post_context', 'source_url', 'source_description', 'source_type', 'order'],
    });

    const chunks = searchResultsToChunks(results);
    const sources = getSourcesFromChunks(chunks);
    const context = getContextFromSources(sources);
    
    // Extract distinct company names from the chunk text where lines start with "Company: <Name>"
    const companySet = new Set<string>();
    for (const chunk of chunks) {
        const match = chunk.text.match(/Company:\s*(.+)/);
        if (match && match[1]) {
            companySet.add(match[1].trim());
        }
    }

    const companies = Array.from(companySet);

    return {
        context: `<results> ${context} </results>`,
        companies,
    };
}
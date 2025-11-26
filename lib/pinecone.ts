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

export type PlacementNamespacesResult = {
    placementsContext: string;
    placementCompanies: string[];
    placementStatsContext: string;
};

async function searchPlacementsNamespace(query: string): Promise<{ context: string; companies: string[] }> {
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
    if (chunks.length === 0) {
        return { context: '', companies: [] };
    }

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

    return {
        context: `<placements_results> ${context} </placements_results>`,
        companies: Array.from(companySet),
    };
}

async function searchPlacementStatsNamespace(query: string): Promise<string> {
    const results = await pineconeIndex.namespace('placement_stats').searchRecords({
        query: {
            inputs: {
                text: query,
            },
            topK: PINECONE_TOP_K,
        },
        fields: ['text', 'name', 'company', 'ctc', 'status', 'yoe'],
    });

    // For stats we don't need chunk-level stitching; the "text" field already contains a readable summary.
    const records: any[] = (results as any)?.records ?? (results as any)?.result?.hits ?? [];
    if (!Array.isArray(records) || records.length === 0) {
        return '';
    }

    const lines: string[] = [];
    for (const record of records) {
        const fields = record.fields || record.values || record.data || {};
        const text = fields.text || record.text || '';
        if (text) {
            lines.push(String(text));
        }
    }

    if (lines.length === 0) {
        return '';
    }

    return `<placement_stats_results>
${lines.join('\n')}
</placement_stats_results>`;
}

export async function searchPinecone(
    query: string,
): Promise<PlacementNamespacesResult> {
    const [placements, placementStats] = await Promise.all([
        searchPlacementsNamespace(query),
        searchPlacementStatsNamespace(query),
    ]);

    return {
        placementsContext: placements.context,
        placementCompanies: placements.companies,
        placementStatsContext: placementStats,
    };
}
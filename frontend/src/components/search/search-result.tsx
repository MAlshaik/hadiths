import { searchHadithsByVector, getSources } from "@/server/db/queries/hadiths";
import { HadithCard } from "@/components/hadiths/hadith-card";
import { PaginationControls } from "@/components/pagination-controls";

interface SearchResultsProps {
  query: string;
  sourceId?: number;
  page: number;
}

export async function SearchResults({ query, sourceId, page = 1 }: SearchResultsProps) {
  const limit = 10;
  let result;
  let sources;
  
  try {
    sources = await getSources();
    
    // Use vector search API instead of direct database query
    result = await searchHadithsByVector(query, page, limit);
    
    // Filter by source if specified
    if (sourceId) {
      result.hadiths = result.hadiths.filter(hadith => hadith.source_id === sourceId);
      result.totalCount = result.hadiths.length;
    }
  } catch (error) {
    return (
      <div className="text-center py-12">
        <h3 className="text-lg font-semibold">Error performing search</h3>
        <p className="text-muted-foreground">Please try again later</p>
      </div>
    );
  }
  
  const { hadiths, totalCount } = result;
  const totalPages = Math.ceil(totalCount / limit);
  const sourceMap = Object.fromEntries(sources.map(source => [source.id, source]));
  
  // Display message if no results found
  if (hadiths.length === 0) {
    return (
      <div className="text-center py-12">
        <h3 className="text-lg font-semibold">No results found</h3>
        <p className="text-muted-foreground">
          Try using different keywords or removing filters
        </p>
      </div>
    );
  }
  
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold">
          {totalCount} {totalCount === 1 ? 'result' : 'results'} for "{query}"
        </h2>
      </div>
      
      <div className="space-y-4">
        {hadiths.map((hadith) => (
          <HadithCard 
            key={hadith.id} 
            hadith={hadith} 
            source={sourceMap[hadith.source_id]}
          />
        ))}
      </div>
      
      {totalPages > 1 && (
        <PaginationControls 
          currentPage={page} 
          totalPages={totalPages} 
          sourceId={sourceId} 
          query={query}
        />
      )}
    </div>
  );
}
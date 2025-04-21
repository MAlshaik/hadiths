import { findSimilarHadiths, getHadithById, getSources } from "@/server/db/queries/hadiths";
import { HadithCard } from "@/components/hadiths/hadith-card";
import { PaginationControls } from "@/components/pagination-controls";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";
import { Hadith } from "@/types/hadith";

interface SimilarHadithsResultsProps {
  hadithId: number;
  page: number;
}

export async function SimilarHadithsResults({ 
  hadithId, 
  page = 1
}: SimilarHadithsResultsProps) {
  const limit = 10;
  
  try {
    // Fetch the original hadith
    const originalHadith = await getHadithById(hadithId);
    
    if (!originalHadith) {
      return (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>
            Could not find the original hadith with ID {hadithId}.
          </AlertDescription>
        </Alert>
      );
    }
    
    // Fetch similar hadiths
    const result = await findSimilarHadiths(
      hadithId, 
      page, 
      limit
    );
    
    // Fetch all sources for reference
    const sources = await getSources();
    const sourceMap = Object.fromEntries(sources.map(source => [source.id, source]));
    
    const { hadiths, total_count } = result;
    const totalPages = Math.ceil(total_count / limit);
    
    // Display message if no results found
    if (hadiths.length === 0) {
      return (
        <div className="space-y-6">
          <div className="mb-8 p-6 border rounded-lg">
            <h3 className="text-lg font-semibold mb-2">Original Hadith</h3>
            <HadithCard 
              hadith={originalHadith} 
              source={sourceMap[originalHadith.source_id]} 
            />
          </div>
          
          <div className="text-center py-12">
            <h3 className="text-lg font-semibold">No similar hadiths found</h3>
            <p className="text-muted-foreground">
              No semantically similar hadiths were found in the database
            </p>
          </div>
        </div>
      );
    }
    
    return (
      <div className="space-y-6">
        <div className="mb-8 p-6 border rounded-lg">
          <h3 className="text-lg font-semibold mb-2">Original Hadith</h3>
          <HadithCard 
            hadith={originalHadith} 
            source={sourceMap[originalHadith.source_id]} 
          />
        </div>
        
        <div>
          <h2 className="text-xl font-bold mb-4">
            {total_count} Similar {total_count === 1 ? 'Hadith' : 'Hadiths'}
          </h2>
          
          <div className="space-y-4">
            {hadiths.map((hadith: Hadith) => (
              <div key={hadith.id} className="relative">
                <div className="absolute -left-4 top-4 bg-primary text-primary-foreground text-xs px-2 py-1 rounded-md">
                  {(hadith.similarity || 0 * 100).toFixed(1)}%
                </div>
                <HadithCard 
                  hadith={hadith} 
                  source={sourceMap[hadith.source_id]}
                />
              </div>
            ))}
          </div>
        </div>
        
        {totalPages > 1 && (
          <PaginationControls 
            currentPage={page} 
            totalPages={totalPages}
            baseUrl={`/similar?hadith=${hadithId}`}
          />
        )}
      </div>
    );
  } catch (error) {
    console.error("Error fetching similar hadiths:", error);
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>
          Failed to fetch similar hadiths. Please try again later.
        </AlertDescription>
      </Alert>
    );
  }
}

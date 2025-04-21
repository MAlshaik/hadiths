import Link from "next/link";
import { 
  getHadiths, 
  getHadithsBySource, 
  getHadithsByBook, 
  getHadithsByChapter,
  getSources
} from "@/server/db/queries/hadiths";
import { HadithCard } from "@/components/hadiths/hadith-card";
import { PaginationControls } from "@/components/pagination-controls";

interface HadithBrowserProps {
  sourceId?: number;
  book?: number;
  chapter?: number;
  page: number;
}

export async function HadithBrowser({ 
  sourceId, 
  book, 
  chapter, 
  page = 1 
}: HadithBrowserProps) {
  const limit = 10;
  let result;
  let sources;

  try {
    sources = await getSources();
    
    if (sourceId && book && chapter) {
      result = await getHadithsByChapter(sourceId, book, chapter, page, limit);
    } else if (sourceId && book) {
      result = await getHadithsByBook(sourceId, book, page, limit);
    } else if (sourceId) {
      result = await getHadithsBySource(sourceId, page, limit);
    } else {
      result = await getHadiths(page, limit);
    }
  } catch (error) {
    return (
      <div className="text-center py-12">
        <h3 className="text-lg font-semibold">Error loading hadiths</h3>
        <p className="text-muted-foreground">Please try again later</p>
      </div>
    );
  }

  const { hadiths, totalCount } = result;
  const totalPages = Math.ceil(totalCount / limit);
  const sourceMap = Object.fromEntries(sources.map(source => [source.id, source]));

  // Display message if no hadiths are found
  if (hadiths.length === 0) {
    return (
      <div className="text-center py-12">
        <h3 className="text-lg font-semibold">No hadiths found</h3>
        <p className="text-muted-foreground">Try changing your filters</p>
        <Link 
          href="/hadiths" 
          className="inline-block mt-4 text-primary hover:underline"
        >
          Clear all filters
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold">
          {totalCount} {totalCount === 1 ? 'Hadith' : 'Hadiths'} Found
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
          book={book} 
          chapter={chapter} 
        />
      )}
    </div>
  );
}
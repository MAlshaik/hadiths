import { Suspense } from "react";
import { Metadata } from "next";
import { SimilarHadithsResults } from "@/components/similar/similar-results";
import { SimilarHadithsFilters } from "@/components/similar/similar-filters";
import { SearchResultsSkeleton } from "@/components/search/search-results-skeleton";

export const metadata: Metadata = {
  title: "Similar Hadiths",
  description: "Find hadiths similar to a selected hadith using vector embeddings",
};

export default async function SimilarHadithsPage({
  searchParams,
}: {
  searchParams: {
    hadith?: string;
    page?: string;
  }
}) {
  const hadithId = searchParams.hadith ? parseInt(searchParams.hadith) : undefined;
  const page = searchParams.page ? parseInt(searchParams.page) : 1;
  
  return (
    <div className="p-24">
      <h1 className="mb-6 scroll-m-20 text-3xl font-extrabold tracking-tight lg:text-4xl">
        Similar Hadiths
      </h1>
      
      {hadithId ? (
        <div className="grid grid-cols-1 md:grid-cols-[250px_1fr] gap-6">
          <aside>
            <SimilarHadithsFilters 
              hadithId={hadithId}
            />
          </aside>
          
          <main>
            <Suspense fallback={<SearchResultsSkeleton />}>
              <SimilarHadithsResults 
                hadithId={hadithId}
                page={page}
              />
            </Suspense>
          </main>
        </div>
      ) : (
        <div className="text-center py-16">
          <h2 className="text-2xl font-bold mb-2">No Hadith Selected</h2>
          <p className="text-muted-foreground max-w-md mx-auto">
            Please select a hadith to find similar hadiths. You can do this by clicking the "Similar" button on any hadith card.
          </p>
        </div>
      )}
    </div>
  );
}

import { Suspense } from "react";
import { Metadata } from "next";
import { SearchResults } from "@/components/search/search-result";
import { SearchForm } from "@/components/search/search-form";
import { SearchFilters } from "@/components/search/search-filters";
import { SearchResultsSkeleton } from "@/components/search/search-results-skeleton";

export const metadata: Metadata = {
  title: "Search Hadiths",
  description: "Search across hadith collections from various books",
};

export default function SearchPage({
  searchParams,
}: {
  searchParams: {
    q?: string;
    source?: string;
    page?: string;
  };
}) {
  const query = searchParams.q || "";
  const sourceId = searchParams.source ? parseInt(searchParams.source) : undefined;
  const page = searchParams.page ? parseInt(searchParams.page) : 1;
  
  return (
    <div className="p-24">
      <h1 className="mb-6 scroll-m-20 text-3xl font-extrabold tracking-tight lg:text-4xl">
        Search Hadiths
      </h1>
      
      <div className="mb-8">
        <SearchForm initialQuery={query} />
      </div>
      
      {query && (
        <div className="grid grid-cols-1 md:grid-cols-[250px_1fr] gap-6">
          <aside>
            <SearchFilters sourceId={sourceId} />
          </aside>
          
          <main>
            <Suspense fallback={<SearchResultsSkeleton />}>
              <SearchResults query={query} sourceId={sourceId} page={page} />
            </Suspense>
          </main>
        </div>
      )}
      
      {!query && (
        <div className="text-center py-16">
          <h2 className="text-2xl font-bold mb-2">Begin Your Search</h2>
          <p className="text-muted-foreground max-w-md mx-auto">
            Enter keywords to search across all hadith collections in our database.
          </p>
        </div>
      )}
    </div>
  );
}
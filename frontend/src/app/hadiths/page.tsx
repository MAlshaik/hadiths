import { Suspense } from "react";
import { Metadata } from "next";
import { HadithBrowser } from "@/components/hadiths/hadith-browser";
import { HadithListSkeleton } from "@/components/hadiths/hadith-list-skeleton";
import { HadithFilters } from "@/components/hadiths/hadith-fiters";

export const metadata: Metadata = {
  title: "Browse Hadiths",
  description: "Browse and filter hadiths from various book collections",
};

export default function HadithsPage({
  searchParams,
}: {
  searchParams: {
    source?: string;
    book?: string;
    chapter?: string;
    page?: string;
  };
}) {
  const sourceId = searchParams.source ? parseInt(searchParams.source) : undefined;
  const book = searchParams.book ? parseInt(searchParams.book) : undefined;
  const chapter = searchParams.chapter ? parseInt(searchParams.chapter) : undefined;
  const page = searchParams.page ? parseInt(searchParams.page) : 1;

  return (
    <div className="p-24">
      <h1 className="mb-6 scroll-m-20 text-3xl font-extrabold tracking-tight lg:text-4xl">
        Browse Hadiths
      </h1>
      
      <div className="grid grid-cols-1 md:grid-cols-[300px_1fr] gap-6">
        <aside>
          <HadithFilters 
            sourceId={sourceId} 
            book={book} 
            chapter={chapter} 
          />
        </aside>
        
        <main>
          <Suspense fallback={<HadithListSkeleton />}>
            <HadithBrowser
              sourceId={sourceId}
              book={book}
              chapter={chapter}
              page={page}
            />
          </Suspense>
        </main>
      </div>
    </div>
  );
}
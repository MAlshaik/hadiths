import { Suspense } from "react";
import { Metadata } from "next";
import { HadithCompare } from "@/components/compare/hadith-compare";
import { HadithCompareSkeleton } from "@/components/compare/hadith-compare-skeleton";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export const metadata: Metadata = {
  title: "Compare Hadiths",
  description: "Find and compare similar hadiths across traditions",
};

export default function ComparePage({
  searchParams,
}: {
  searchParams: {
    hadith?: string;
  };
}) {
  const hadithId = searchParams.hadith ? parseInt(searchParams.hadith) : undefined;
  
  return (
    <div className="p-24">
      <h1 className="mb-6 scroll-m-20 text-3xl font-extrabold tracking-tight lg:text-4xl">
        Compare Hadiths
      </h1>
      
      {hadithId ? (
        <Suspense fallback={<HadithCompareSkeleton />}>
          <HadithCompare hadithId={hadithId} />
        </Suspense>
      ) : (
        <Card className="max-w-3xl mx-auto">
          <CardHeader>
            <CardTitle>Find Similar Hadiths</CardTitle>
          </CardHeader>
          <CardContent className="text-center py-8">
            <p className="text-muted-foreground mb-6">
              To compare hadiths, first browse or search for a hadith, then click the
              &quot;Compare&quot; button to find similar narratives across traditions.
            </p>
            <div className="flex flex-col items-center space-y-4">
              <p className="font-medium">Select a hadith to start comparing:</p>
              <div className="flex gap-4">
                <a 
                  href="/hadiths" 
                  className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground ring-offset-background transition-colors hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50"
                >
                  Browse Hadiths
                </a>
                <a 
                  href="/search" 
                  className="inline-flex h-10 items-center justify-center rounded-md border border-input bg-background px-4 py-2 text-sm font-medium ring-offset-background transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50"
                >
                  Search Collections
                </a>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
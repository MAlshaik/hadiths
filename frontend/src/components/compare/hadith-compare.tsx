import Link from "next/link";
import { notFound } from "next/navigation";
import { getHadithById, getSources } from "@/server/db/queries/hadiths";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { ArrowLeft, BookOpen, RotateCw } from "lucide-react";

// This would be implemented in your production system
// Here we're just using placeholder logic
async function findSimilarHadiths(hadithId: number) {
  // In a real implementation, this would use vector similarity search
  // For now, we'll just return some placeholder data
  
  // Get the source hadith
  const sourceHadith = await getHadithById(hadithId);
  if (!sourceHadith) return [];
  
  // Get all sources
  const sources = await getSources();
  
  // Find the current source and other collections
  const currentSource = sources.find(s => s.id === sourceHadith.source_id);
  if (!currentSource) return [];
  
  // Get sources from other collections
  const otherSources = sources.filter(s => s.id !== currentSource.id);
  
  if (otherSources.length === 0) return [];
  
  // For now, just return placeholder "similar" hadiths
  // In production, this would be actual similarity search results
  return [
    {
      id: 9999,
      source_id: otherSources[0].id,
      volume: 1,
      book: 1,
      chapter: 1,
      number: 1,
      arabic_text: "نص عربي للحديث المشابه",
      english_text: "This is a placeholder for a similar hadith from another collection that would be found using vector similarity search in production.",
      narrator_chain: "Placeholder narrator chain",
      topics: ["faith", "belief"],
      created_at: new Date(),
      similarity_score: 0.85,
    }
  ];
}

interface HadithCompareProps {
  hadithId: number;
}

export async function HadithCompare({ hadithId }: HadithCompareProps) {
  const hadith = await getHadithById(hadithId);
  
  if (!hadith) {
    notFound();
  }
  
  const sources = await getSources();
  const source = sources.find(s => s.id === hadith.source_id);
  
  if (!source) {
    notFound();
  }
  
  // Find similar hadiths
  const similarHadiths = await findSimilarHadiths(hadithId);
  
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" size="sm" asChild>
          <Link href="/hadiths">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Hadiths
          </Link>
        </Button>
        
        <Button variant="outline" size="sm" asChild>
          <Link href={`/hadiths/${hadithId}`}>
            <BookOpen className="h-4 w-4 mr-2" />
            View Full Details
          </Link>
        </Button>
      </div>
      
      <Tabs defaultValue="compare" className="w-full">
        <TabsList className="mb-4">
          <TabsTrigger value="compare">Compare View</TabsTrigger>
          <TabsTrigger value="source">Source Hadith</TabsTrigger>
        </TabsList>
        
        <TabsContent value="compare" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Source Hadith */}
            <div className="flex flex-col">
              <div className="bg-primary/10 text-primary p-2 rounded-t-md">
                <div className="flex justify-between items-center">
                  <h3 className="font-semibold">{source.name}</h3>
                  <span className="text-sm">Collection</span>
                </div>
              </div>
              
              <Card className="rounded-t-none flex-1">
                <CardContent className="p-4 space-y-4">
                  <div className="text-sm text-muted-foreground">
                    Book {hadith.book}, Chapter {hadith.chapter}, No. {hadith.number}
                  </div>
                  
                  {hadith.arabic_text && (
                    <div className="p-3 bg-muted rounded-md text-right font-arabic text-lg leading-loose" dir="rtl">
                      {hadith.arabic_text}
                    </div>
                  )}
                  
                  <div className="leading-relaxed">
                    {hadith.english_text}
                  </div>
                  
                  {hadith.narrator_chain && (
                    <div className="text-sm text-muted-foreground italic">
                      <strong>Narrators:</strong> {hadith.narrator_chain}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
            
            {/* Similar Hadiths */}
            <div className="flex flex-col">
              {similarHadiths.length > 0 ? (
                similarHadiths.map((similarHadith) => {
                  const similarSource = sources.find(s => s.id === similarHadith.source_id);
                  
                  return (
                    <div key={similarHadith.id} className="flex flex-col h-full">
                      <div className="bg-secondary/80 text-secondary-foreground p-2 rounded-t-md">
                        <div className="flex justify-between items-center">
                          <h3 className="font-semibold">{similarSource?.name}</h3>
                          <span className="text-sm">Collection</span>
                        </div>
                      </div>
                      
                      <Card className="rounded-t-none flex-1">
                        <CardContent className="p-4 space-y-4">
                          <div className="flex justify-between items-center">
                            <div className="text-sm text-muted-foreground">
                              Book {similarHadith.book}, Chapter {similarHadith.chapter}, No. {similarHadith.number}
                            </div>
                            <div className="text-sm font-medium text-primary">
                              {(similarHadith.similarity_score * 100).toFixed(0)}% Similar
                            </div>
                          </div>
                          
                          {similarHadith.arabic_text && (
                            <div className="p-3 bg-muted rounded-md text-right font-arabic text-lg leading-loose" dir="rtl">
                              {similarHadith.arabic_text}
                            </div>
                          )}
                          
                          <div className="leading-relaxed">
                            {similarHadith.english_text}
                          </div>
                          
                          {similarHadith.narrator_chain && (
                            <div className="text-sm text-muted-foreground italic">
                              <strong>Narrators:</strong> {similarHadith.narrator_chain}
                            </div>
                          )}
                          
                          <div className="flex justify-end">
                            <Button variant="outline" size="sm" asChild>
                              <Link href={`/hadiths/${similarHadith.id}`}>
                                View Details
                              </Link>
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    </div>
                  );
                })
              ) : (
                <Card className="h-full flex flex-col justify-center items-center p-8 text-center">
                  <CardTitle className="mb-2">No Similar Hadiths Found</CardTitle>
                  <p className="text-muted-foreground">
                    We couldn&apos;t find similar hadiths in other collections for this query.
                  </p>
                  <Button variant="outline" asChild>
                    <Link href="/hadiths">
                      <RotateCw className="h-4 w-4 mr-2" />
                      Try Another Hadith
                    </Link>
                  </Button>
                </Card>
              )}
            </div>
          </div>
        </TabsContent>
        
        <TabsContent value="source">
          <Card className="max-w-3xl mx-auto">
            <CardHeader>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <CardTitle>
                    {source.name} - Hadith #{hadith.number}
                  </CardTitle>
                  <p className="text-sm text-muted-foreground">
                    Book Collection
                  </p>
                </div>
                <div className="text-sm text-muted-foreground">
                  <div>Book {hadith.book}</div>
                  <div>Chapter {hadith.chapter}</div>
                  <div>Volume {hadith.volume}</div>
                </div>
              </div>
            </CardHeader>
            
            <CardContent className="space-y-4">
              {hadith.arabic_text && (
                <>
                  <div className="p-4 bg-muted rounded-md text-right font-arabic text-xl leading-loose" dir="rtl">
                    {hadith.arabic_text}
                  </div>
                  <Separator />
                </>
              )}
              
              <div className="leading-relaxed text-lg">
                {hadith.english_text}
              </div>
              
              {hadith.narrator_chain && (
                <div className="p-4 bg-muted rounded-md mt-4">
                  <h3 className="font-semibold mb-2">Narrators:</h3>
                  <p className="text-muted-foreground">
                    {hadith.narrator_chain}
                  </p>
                </div>
              )}
              
              {hadith.topics && hadith.topics.length > 0 && (
                <div className="mt-4">
                  <h3 className="font-semibold mb-2">Topics:</h3>
                  <div className="flex flex-wrap gap-2">
                    {hadith.topics.map((topic, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center bg-secondary text-secondary-foreground rounded-full px-2.5 py-0.5"
                      >
                        {topic}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
import { Suspense } from "react";
import { Metadata } from "next";
import { notFound } from "next/navigation";
import Link from "next/link";
import { getHadithById, getSources } from "@/server/db/queries/hadiths";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { HadithDetailSkeleton } from "@/components/hadiths/hadith-detail-skeleton";
import { ArrowLeft, BookOpen, ArrowUpRight } from "lucide-react";

interface HadithDetailPageProps {
  params: {
    id: string;
  };
}

export async function generateMetadata({
  params,
}: HadithDetailPageProps): Promise<Metadata> {
  const id = parseInt(params.id);
  const hadith = await getHadithById(id);
  
  if (!hadith) {
    return {
      title: "Hadith Not Found",
    };
  }
  
  const text = hadith.english_text.slice(0, 100) + (hadith.english_text.length > 100 ? '...' : '');
  
  return {
    title: `Hadith ${hadith.number} | Book ${hadith.book}`,
    description: text,
  };
}

export default async function HadithDetailPage({ params }: HadithDetailPageProps) {
  const id = parseInt(params.id);
  
  return (
    <div className="p-24">
      <div className="mb-6">
        <Button variant="ghost" asChild>
          <Link href="/hadiths">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Hadiths
          </Link>
        </Button>
      </div>
      
      <Suspense fallback={<HadithDetailSkeleton />}>
        <HadithDetail id={id} />
      </Suspense>
    </div>
  );
}

async function HadithDetail({ id }: { id: number }) {
  const hadith = await getHadithById(id);
  
  if (!hadith) {
    notFound();
  }
  
  const sources = await getSources();
  const source = sources.find(s => s.id === hadith.source_id);
  
  if (!source) {
    notFound();
  }
  
  return (
    <Card className="overflow-hidden max-w-4xl mx-auto">
      <CardHeader className="pb-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              Hadith #{hadith.number}
            </h1>
            <p className="text-muted-foreground">
              <BookOpen className="h-4 w-4 inline mr-1" />
              {source.name} • {source.tradition} Tradition
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
      
      <CardFooter className="flex justify-between border-t pt-6">
        <Button variant="outline" asChild>
          <Link href={`/hadiths?source=${source.id}&book=${hadith.book}&chapter=${hadith.chapter}`}>
            <BookOpen className="h-4 w-4 mr-2" />
            View Chapter
          </Link>
        </Button>
        
        <Button asChild>
          <Link href={`/compare?hadith=${hadith.id}`}>
            <ArrowUpRight className="h-4 w-4 mr-2" />
            Find Similar Hadiths
          </Link>
        </Button>
      </CardFooter>
    </Card>
  );
}
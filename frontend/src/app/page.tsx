import Link from "next/link";
import { getSources } from "@/server/db/queries/hadiths";
import { Button } from "@/components/ui/button";
import { ArrowRight, BookOpen } from "lucide-react";

export default async function Home() {
  const sources = await getSources();

  return (
    <div className=" flex flex-col items-center justify-center py-8 md:py-12">
      <div className="mx-auto max-w-[850px] flex flex-col items-center justify-center text-center gap-4">
        <h1 className="scroll-m-20 text-4xl font-extrabold tracking-tight lg:text-5xl">
          Cross-Tradition Hadith Explorer
        </h1>
        <p className="text-xl text-muted-foreground">
          Discover and compare hadiths from various book collections.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 mt-6">
          <Button size="lg" asChild>
            <Link href="/hadiths">
              Browse Hadiths <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
          <Button size="lg" variant="outline" asChild>
            <Link href="/search">
              Search Collections <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-16 w-full max-w-[1000px]">
        {sources.map((source) => (
          <div key={source.id} className="rounded-lg border bg-card text-card-foreground shadow-sm">
            <div className="flex flex-col space-y-1.5 p-6">
              <h3 className="text-2xl font-semibold tracking-tight">{source.name}</h3>
              <p className="text-sm text-muted-foreground">
                {source.tradition} tradition • {source.compiler}
              </p>
            </div>
            <div className="p-6 pt-0">
              <p className="mb-4">{source.description}</p>
              <Button variant="outline" className="w-full" asChild>
                <Link href={`/hadiths?source=${source.id}`}>
                  <BookOpen className="mr-2 h-4 w-4" />
                  View Collection
                </Link>
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
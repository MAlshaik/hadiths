"use client";

import { useState } from "react";
import Link from "next/link";
import { Hadith, Source } from "@/types/hadith";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { 
  FileText, 
  ChevronDown, 
  ChevronUp,
  BookOpen,
  Search
} from "lucide-react";

interface HadithCardProps {
  hadith: Hadith;
  source: Source;
}

export function HadithCard({ hadith, source }: HadithCardProps) {
  const [expanded, setExpanded] = useState(false);
  
  const toggleExpand = () => setExpanded(!expanded);
  
  const hasArabicText = !!hadith.arabic_text;
  const hasNarratorChain = !!hadith.narrator_chain;
  
  return (
    <Card className="overflow-hidden transition-all duration-200">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">
              <BookOpen className="h-3 w-3 inline mr-1" />
              {source.name}
            </span>
          </div>
          <div className="text-sm font-medium text-muted-foreground">
            Vol. {hadith.volume}, Book {hadith.book}, Ch. {hadith.chapter}, No. {hadith.number}
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="text-sm pb-3">
        {hasArabicText && expanded && (
          <div className="mb-4 text-right font-arabic text-xl leading-loose" dir="rtl">
            {hadith.arabic_text}
          </div>
        )}
        
        <div className="leading-relaxed">
          {expanded ? hadith.english_text : (
            hadith.english_text.length > 280 ? 
              hadith.english_text.substring(0, 280) + "..." : 
              hadith.english_text
          )}
        </div>
        
        {hasNarratorChain && expanded && (
          <div className="mt-4 text-sm text-muted-foreground italic">
            <strong>Narrators:</strong> {hadith.narrator_chain}
          </div>
        )}
        
        {hadith.topics && hadith.topics.length > 0 && expanded && (
          <div className="mt-4 flex flex-wrap gap-2">
            {hadith.topics.map((topic, index) => (
              <span 
                key={index}
                className="inline-flex items-center bg-secondary text-secondary-foreground text-xs rounded-full px-2.5 py-0.5"
              >
                {topic}
              </span>
            ))}
          </div>
        )}
      </CardContent>
      
      <CardFooter className="flex justify-between pt-0">
        <Button variant="ghost" size="sm" onClick={toggleExpand}>
          {expanded ? (
            <>
              <ChevronUp className="h-4 w-4 mr-2" />
              Show Less
            </>
          ) : (
            <>
              <ChevronDown className="h-4 w-4 mr-2" />
              Show More
            </>
          )}
        </Button>
        
        <div className="flex gap-2">
          <Button variant="outline" size="sm" asChild>
            <Link href={`/hadiths/${hadith.id}`}>
              <FileText className="h-4 w-4 mr-2" />
              Details
            </Link>
          </Button>
          <Button variant="outline" size="sm" asChild>
            <Link href={`/similar?hadith=${hadith.id}`}>
              <Search className="h-4 w-4 mr-2" />
              Similar
            </Link>
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
}
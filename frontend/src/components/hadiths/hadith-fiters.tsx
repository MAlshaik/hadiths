"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { 
  getSources,
  getBooksBySource,
  getChaptersByBook
} from "@/server/db/queries/hadiths";
import { Source } from "@/types/hadith";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Loader2, X } from "lucide-react";

interface HadithFiltersProps {
  sourceId?: number;
  book?: number;
  chapter?: number;
}

export function HadithFilters({ sourceId, book, chapter }: HadithFiltersProps) {
  const router = useRouter();
  const pathname = usePathname();
  
  const [sources, setSources] = useState<Source[]>([]);
  const [books, setBooks] = useState<number[]>([]);
  const [chapters, setChapters] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [selectedSource, setSelectedSource] = useState<number | undefined>(sourceId);
  const [selectedBook, setSelectedBook] = useState<number | undefined>(book);
  const [selectedChapter, setSelectedChapter] = useState<number | undefined>(chapter);
  
  // Fetch sources on component mount
  useEffect(() => {
    const fetchSources = async () => {
      try {
        const sourcesData = await getSources();
        setSources(sourcesData);
        setLoading(false);
      } catch (error) {
        console.error("Failed to fetch sources:", error);
        setLoading(false);
      }
    };
    
    fetchSources();
  }, []);
  
  // Fetch books when source changes
  useEffect(() => {
    const fetchBooks = async () => {
      if (!selectedSource) {
        setBooks([]);
        return;
      }
      
      try {
        const booksData = await getBooksBySource(selectedSource);
        setBooks(booksData);
        
        // Reset book if the current selection is not available
        if (selectedBook && !booksData.includes(selectedBook)) {
          setSelectedBook(undefined);
        }
      } catch (error) {
        console.error("Failed to fetch books:", error);
      }
    };
    
    fetchBooks();
  }, [selectedSource, selectedBook]);
  
  // Fetch chapters when book changes
  useEffect(() => {
    const fetchChapters = async () => {
      if (!selectedSource || !selectedBook) {
        setChapters([]);
        return;
      }
      
      try {
        const chaptersData = await getChaptersByBook(selectedSource, selectedBook);
        setChapters(chaptersData);
        
        // Reset chapter if the current selection is not available
        if (selectedChapter && !chaptersData.includes(selectedChapter)) {
          setSelectedChapter(undefined);
        }
      } catch (error) {
        console.error("Failed to fetch chapters:", error);
      }
    };
    
    fetchChapters();
  }, [selectedSource, selectedBook, selectedChapter]);
  
  // Apply filters
  const applyFilters = () => {
    const params = new URLSearchParams();
    
    if (selectedSource !== undefined) {
      params.set("source", selectedSource.toString());
    }
    
    if (selectedBook !== undefined) {
      params.set("book", selectedBook.toString());
    }
    
    if (selectedChapter !== undefined) {
      params.set("chapter", selectedChapter.toString());
    }
    
    // Reset to page 1 when filters change
    params.set("page", "1");
    
    router.push(`${pathname}?${params.toString()}`);
  };
  
  // Clear all filters
  const clearFilters = () => {
    setSelectedSource(undefined);
    setSelectedBook(undefined);
    setSelectedChapter(undefined);
    router.push(pathname);
  };
  
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent className="flex justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }
  
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          Filters
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={clearFilters}
            disabled={!selectedSource && !selectedBook && !selectedChapter}
          >
            <X className="h-4 w-4 mr-1" /> Clear
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="source">Collection</Label>
          <Select
            value={selectedSource?.toString() || ""}
            onValueChange={(value) => {
              setSelectedSource(value ? parseInt(value) : undefined);
              setSelectedBook(undefined);
              setSelectedChapter(undefined);
            }}
          >
            <SelectTrigger id="source">
              <SelectValue placeholder="Select collection" />
            </SelectTrigger>
            <SelectContent>
              {sources.map((source) => (
                <SelectItem key={source.id} value={source.id.toString()}>
                  {source.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        
        <div className="space-y-2">
          <Label htmlFor="book">Book</Label>
          <Select
            value={selectedBook?.toString() || ""}
            onValueChange={(value) => {
              setSelectedBook(value ? parseInt(value) : undefined);
              setSelectedChapter(undefined);
            }}
            disabled={!selectedSource || books.length === 0}
          >
            <SelectTrigger id="book">
              <SelectValue placeholder="Select book" />
            </SelectTrigger>
            <SelectContent>
              {books.map((bookNumber) => (
                <SelectItem key={bookNumber} value={bookNumber.toString()}>
                  Book {bookNumber}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        
        <div className="space-y-2">
          <Label htmlFor="chapter">Chapter</Label>
          <Select
            value={selectedChapter?.toString() || ""}
            onValueChange={(value) => {
              setSelectedChapter(value ? parseInt(value) : undefined);
            }}
            disabled={!selectedBook || chapters.length === 0}
          >
            <SelectTrigger id="chapter">
              <SelectValue placeholder="Select chapter" />
            </SelectTrigger>
            <SelectContent>
              {chapters.map((chapterNumber) => (
                <SelectItem key={chapterNumber} value={chapterNumber.toString()}>
                  Chapter {chapterNumber}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        
        <Button 
          className="w-full" 
          onClick={applyFilters}
          disabled={
            (selectedSource === sourceId) && 
            (selectedBook === book) && 
            (selectedChapter === chapter)
          }
        >
          Apply Filters
        </Button>
      </CardContent>
    </Card>
  );
}
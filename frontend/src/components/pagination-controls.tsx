"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight, MoreHorizontal } from "lucide-react";

interface PaginationControlsProps {
  currentPage: number;
  totalPages: number;
  sourceId?: number;
  book?: number;
  chapter?: number;
  query?: string;
  hadithId?: number;
  baseUrl?: string;
}

export function PaginationControls({
  currentPage,
  totalPages,
  sourceId,
  book,
  chapter,
  query,
  hadithId,
  baseUrl,
}: PaginationControlsProps) {
  const pathname = usePathname();
  
  // Generate the query string for the pagination links
  const getPageHref = (page: number) => {
    // If a baseUrl is provided, use it instead of building from parameters
    if (baseUrl) {
      const url = new URL(baseUrl, window.location.origin);
      url.searchParams.set("page", page.toString());
      return url.pathname + url.search;
    }
    
    const params = new URLSearchParams();
    params.set("page", page.toString());
    
    if (query !== undefined) {
      params.set("q", query);
    }
    
    if (sourceId !== undefined) {
      params.set("source", sourceId.toString());
    }
    
    if (book !== undefined) {
      params.set("book", book.toString());
    }
    
    if (chapter !== undefined) {
      params.set("chapter", chapter.toString());
    }
    
    if (hadithId !== undefined) {
      params.set("hadith", hadithId.toString());
    }
    

    
    return `${pathname}?${params.toString()}`;
  };
  
  // Determine which page numbers to show
  // Always show first, last, current, and pages around current
  const getVisiblePages = () => {
    const delta = 1; // Number of pages to show before and after current page
    const range: (number | null)[] = [];
    
    // Always include page 1
    range.push(1);
    
    // Calculate the range of pages around the current page
    const rangeStart = Math.max(2, currentPage - delta);
    const rangeEnd = Math.min(totalPages - 1, currentPage + delta);
    
    // Add ellipsis if needed before the range
    if (rangeStart > 2) {
      range.push(null); // ellipsis
    }
    
    // Add the range of pages
    for (let i = rangeStart; i <= rangeEnd; i++) {
      range.push(i);
    }
    
    // Add ellipsis if needed after the range
    if (rangeEnd < totalPages - 1) {
      range.push(null); // ellipsis
    }
    
    // Always include the last page if there is more than one page
    if (totalPages > 1) {
      range.push(totalPages);
    }
    
    return range;
  };
  
  const visiblePages = getVisiblePages();
  
  return (
    <div className="flex items-center justify-center space-x-2 py-4">
      <Button
        variant="outline"
        size="icon"
        disabled={currentPage <= 1}
        asChild={currentPage > 1}
      >
        {currentPage > 1 ? (
          <Link href={getPageHref(currentPage - 1)} aria-label="Previous page">
            <ChevronLeft className="h-4 w-4" />
          </Link>
        ) : (
          <span>
            <ChevronLeft className="h-4 w-4" />
          </span>
        )}
      </Button>
      
      {visiblePages.map((page, index) => {
        if (page === null) {
          return (
            <Button key={`ellipsis-${index}`} variant="ghost" size="icon" disabled>
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          );
        }
        
        return (
          <Button
            key={page}
            variant={currentPage === page ? "default" : "outline"}
            size="icon"
            asChild={currentPage !== page}
          >
            {currentPage !== page ? (
              <Link href={getPageHref(page)} aria-label={`Page ${page}`} aria-current={currentPage === page ? "page" : undefined}>
                {page}
              </Link>
            ) : (
              <span>{page}</span>
            )}
          </Button>
        );
      })}
      
      <Button
        variant="outline"
        size="icon"
        disabled={currentPage >= totalPages}
        asChild={currentPage < totalPages}
      >
        {currentPage < totalPages ? (
          <Link href={getPageHref(currentPage + 1)} aria-label="Next page">
            <ChevronRight className="h-4 w-4" />
          </Link>
        ) : (
          <span>
            <ChevronRight className="h-4 w-4" />
          </span>
        )}
      </Button>
    </div>
  );
}
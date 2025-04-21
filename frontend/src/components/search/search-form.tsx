"use client";

import { useState, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, X } from "lucide-react";

interface SearchFormProps {
  initialQuery: string;
}

export function SearchForm({ initialQuery }: SearchFormProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [query, setQuery] = useState(initialQuery);
  
  // Update the local state when the prop changes
  useEffect(() => {
    setQuery(initialQuery);
  }, [initialQuery]);
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!query.trim()) {
      return;
    }
    
    const params = new URLSearchParams();
    params.set("q", query.trim());
    params.set("page", "1"); // Reset to page 1 on new search
    
    router.push(`${pathname}?${params.toString()}`);
  };
  
  const handleClear = () => {
    setQuery("");
    // Optionally redirect to the search page without query
    router.push(pathname);
  };
  
  return (
    <Card>
      <CardContent className="p-4">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <Input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search by keywords..."
              className="pl-10 pr-10"
            />
            {query && (
              <button
                type="button"
                onClick={handleClear}
                className="absolute right-3 top-3 text-muted-foreground hover:text-foreground"
              >
                <X className="h-4 w-4" />
                <span className="sr-only">Clear</span>
              </button>
            )}
          </div>
          <Button type="submit">Search</Button>
        </form>
      </CardContent>
    </Card>
  );
}
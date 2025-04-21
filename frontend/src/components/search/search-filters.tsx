"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { X, Loader2 } from "lucide-react";
import { getSources } from "@/server/db/queries/hadiths";
import { Source } from "@/types/hadith";

interface SearchFiltersProps {
  sourceId?: number;
}

export function SearchFilters({ sourceId }: SearchFiltersProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSource, setSelectedSource] = useState<string>(
    sourceId ? sourceId.toString() : "all"
  );
  
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
  
  // Update selected source when prop changes
  useEffect(() => {
    setSelectedSource(sourceId ? sourceId.toString() : "all");
  }, [sourceId]);
  
  // Apply source filter
  const applySourceFilter = (value: string) => {
    const params = new URLSearchParams(searchParams);
    
    // Get the current query
    const query = params.get("q") || "";
    
    // Reset params and add the query
    params.delete("source");
    params.set("q", query);
    params.set("page", "1"); // Reset to page 1 when changing filters
    
    if (value !== "all") {
      params.set("source", value);
    }
    
    router.push(`${pathname}?${params.toString()}`);
  };
  
  // Clear all filters
  const clearFilters = () => {
    const params = new URLSearchParams(searchParams);
    const query = params.get("q") || "";
    
    // Keep only the query parameter
    router.push(`${pathname}?q=${encodeURIComponent(query)}`);
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
            disabled={selectedSource === "all"}
          >
            <X className="h-4 w-4 mr-1" /> Clear
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <h3 className="text-sm font-medium mb-3">Collection</h3>
            <RadioGroup
              value={selectedSource}
              onValueChange={(value) => {
                setSelectedSource(value);
                applySourceFilter(value);
              }}
            >
              <div className="flex items-center space-x-2 mb-2">
                <RadioGroupItem value="all" id="all" />
                <Label htmlFor="all" className="cursor-pointer">All Collections</Label>
              </div>
              
              {sources.map((source) => (
                <div key={source.id} className="flex items-center space-x-2 mb-2">
                  <RadioGroupItem value={source.id.toString()} id={`source-${source.id}`} />
                  <Label htmlFor={`source-${source.id}`} className="cursor-pointer">
                    {source.name}
                  </Label>
                </div>
              ))}
            </RadioGroup>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
"use client";

import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { RefreshCw } from "lucide-react";

interface SimilarHadithsFiltersProps {
  hadithId: number;
}

export function SimilarHadithsFilters({
  hadithId
}: SimilarHadithsFiltersProps) {
  const router = useRouter();
  
  // No local state needed for filters
  
  const handleRefresh = () => {
    const searchParams = new URLSearchParams();
    searchParams.append("hadith", hadithId.toString());
    
    router.push(`/similar?${searchParams.toString()}`);
  };
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Filter Similar Hadiths</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-4">
          <h3 className="font-medium">Book Information</h3>
          <p className="text-sm text-muted-foreground">
            Showing similar hadiths across all books based on semantic similarity.
          </p>
        </div>
        
        <Button 
          className="w-full" 
          onClick={handleRefresh}
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh Results
        </Button>
      </CardContent>
    </Card>
  );
}

import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export function HadithCompareSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Skeleton className="h-9 w-36" />
        <Skeleton className="h-9 w-36" />
      </div>
      
      <Tabs defaultValue="compare" className="w-full">
        <TabsList className="mb-4">
          <TabsTrigger value="compare">Compare View</TabsTrigger>
          <TabsTrigger value="source">Source Hadith</TabsTrigger>
        </TabsList>
        
        <TabsContent value="compare" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Source Hadith Skeleton */}
            <div className="flex flex-col">
              <div className="bg-primary/10 p-2 rounded-t-md">
                <div className="flex justify-between items-center">
                  <Skeleton className="h-5 w-32" />
                  <Skeleton className="h-4 w-16" />
                </div>
              </div>
              
              <Card className="rounded-t-none flex-1">
                <CardContent className="p-4 space-y-4">
                  <Skeleton className="h-4 w-40" />
                  
                  <Skeleton className="h-28 w-full" />
                  
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-3/4" />
                  </div>
                  
                  <Skeleton className="h-4 w-full" />
                </CardContent>
              </Card>
            </div>
            
            {/* Similar Hadith Skeleton */}
            <div className="flex flex-col">
              <div className="bg-secondary/80 p-2 rounded-t-md">
                <div className="flex justify-between items-center">
                  <Skeleton className="h-5 w-32" />
                  <Skeleton className="h-4 w-16" />
                </div>
              </div>
              
              <Card className="rounded-t-none flex-1">
                <CardContent className="p-4 space-y-4">
                  <div className="flex justify-between items-center">
                    <Skeleton className="h-4 w-40" />
                    <Skeleton className="h-4 w-24" />
                  </div>
                  
                  <Skeleton className="h-28 w-full" />
                  
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-3/4" />
                  </div>
                  
                  <Skeleton className="h-4 w-full" />
                  
                  <div className="flex justify-end">
                    <Skeleton className="h-9 w-28" />
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>
        
        <TabsContent value="source">
          <Card className="max-w-3xl mx-auto">
            <div className="p-6 pb-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <Skeleton className="h-6 w-48 mb-2" />
                  <Skeleton className="h-4 w-32" />
                </div>
                <div>
                  <Skeleton className="h-4 w-20 mb-1" />
                  <Skeleton className="h-4 w-20 mb-1" />
                  <Skeleton className="h-4 w-20" />
                </div>
              </div>
            </div>
            
            <CardContent className="space-y-4">
              <Skeleton className="h-36 w-full" />
              
              <div className="space-y-2">
                <Skeleton className="h-5 w-full" />
                <Skeleton className="h-5 w-full" />
                <Skeleton className="h-5 w-full" />
                <Skeleton className="h-5 w-full" />
                <Skeleton className="h-5 w-3/4" />
              </div>
              
              <Skeleton className="h-24 w-full" />
              
              <div className="mt-4">
                <Skeleton className="h-6 w-32 mb-2" />
                <div className="flex flex-wrap gap-2">
                  <Skeleton className="h-6 w-16 rounded-full" />
                  <Skeleton className="h-6 w-24 rounded-full" />
                  <Skeleton className="h-6 w-20 rounded-full" />
                  <Skeleton className="h-6 w-28 rounded-full" />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
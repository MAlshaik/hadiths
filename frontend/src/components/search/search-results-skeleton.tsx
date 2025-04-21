import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export function SearchResultsSkeleton() {
  return (
    <div className="space-y-6">
      <div>
        <Skeleton className="h-8 w-72" />
      </div>

      <div className="space-y-4">
        {Array.from({ length: 5 }).map((_, index) => (
          <Card key={index} className="overflow-hidden">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Skeleton className="h-6 w-20" />
                  <Skeleton className="h-4 w-32" />
                </div>
                <Skeleton className="h-4 w-40" />
              </div>
            </CardHeader>
            
            <CardContent className="pb-3">
              <div className="space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
              </div>
            </CardContent>
            
            <CardFooter className="flex justify-between pt-0">
              <Skeleton className="h-9 w-28" />
              <div className="flex gap-2">
                <Skeleton className="h-9 w-24" />
                <Skeleton className="h-9 w-24" />
              </div>
            </CardFooter>
          </Card>
        ))}
      </div>

      <div className="flex items-center justify-center space-x-2 py-4">
        <Skeleton className="h-10 w-10 rounded-md" />
        <Skeleton className="h-10 w-10 rounded-md" />
        <Skeleton className="h-10 w-10 rounded-md" />
        <Skeleton className="h-10 w-10 rounded-md" />
        <Skeleton className="h-10 w-10 rounded-md" />
      </div>
    </div>
  );
}
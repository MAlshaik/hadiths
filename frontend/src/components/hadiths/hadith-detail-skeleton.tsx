import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";

export function HadithDetailSkeleton() {
  return (
    <Card className="overflow-hidden max-w-4xl mx-auto">
      <CardHeader className="pb-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <Skeleton className="h-8 w-48 mb-2" />
            <Skeleton className="h-4 w-32" />
          </div>
          <div>
            <Skeleton className="h-4 w-20 mb-1" />
            <Skeleton className="h-4 w-20 mb-1" />
            <Skeleton className="h-4 w-20" />
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        <Skeleton className="h-36 w-full" />
        <Separator />
        
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
      
      <CardFooter className="flex justify-between border-t pt-6">
        <Skeleton className="h-10 w-32" />
        <Skeleton className="h-10 w-40" />
      </CardFooter>
    </Card>
  );
}
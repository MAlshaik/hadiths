"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { 
  Home, 
  Search, 
  BookOpen, 
  Compass, 
  Menu, 
  X
} from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetTrigger,
  SheetClose
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { getSources } from "@/server/db/queries/hadiths";
import { Source } from "@/types/hadith";
import { ThemeToggle } from "./theme-toggle";

export function Navbar() {
  const pathname = usePathname();
  const [sources, setSources] = useState<Source[]>([]);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  // Toggle dropdown menu
  const toggleDropdown = () => {
    setIsDropdownOpen(!isDropdownOpen);
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = () => {
      if (isDropdownOpen) setIsDropdownOpen(false);
    };

    document.addEventListener("click", handleClickOutside);
    return () => document.removeEventListener("click", handleClickOutside);
  }, [isDropdownOpen]);

  // Fetch sources for the dropdown
  useEffect(() => {
    const fetchSources = async () => {
      try {
        const sourcesData = await getSources();
        setSources(sourcesData);
      } catch (error) {
        console.error("Failed to fetch sources:", error);
      }
    };

    fetchSources();
  }, []);

  // All sources for collections
  const allSources = [...sources];

  // Main navigation items
  const mainNavItems = [
    {
      href: "/",
      label: "Home",
      icon: <Home className="h-4 w-4 mr-2" />,
      active: pathname === "/"
    },
    {
      href: "/hadiths",
      label: "Browse All",
      icon: <BookOpen className="h-4 w-4 mr-2" />,
      active: pathname === "/hadiths" && !pathname.includes("/hadiths/")
    },
    {
      href: "/search",
      label: "Search",
      icon: <Search className="h-4 w-4 mr-2" />,
      active: pathname === "/search"
    }
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-14 items-center justify-between px-24">
        {/* Logo and Brand */}
        <div className="flex items-center">
          <Link href="/" className="flex items-center space-x-2">
            <span className="font-bold text-xl hidden sm:inline-block">Hadith Explorer</span>
            <span className="font-bold text-xl sm:hidden">HE</span>
          </Link>
        </div>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center space-x-1">
          {mainNavItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors",
                item.active 
                  ? "bg-accent text-accent-foreground" 
                  : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
              )}
            >
              {item.icon}
              {item.label}
            </Link>
          ))}

          {/* Collections dropdown */}
          <div className="relative" onClick={(e) => e.stopPropagation()}>
            <Button
              variant="ghost"
              className={cn(
                "flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors",
                pathname.includes("/collections") 
                  ? "bg-accent text-accent-foreground" 
                  : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
              )}
              onClick={toggleDropdown}
            >
              <Compass className="h-4 w-4 mr-2" />
              Collections
            </Button>

            {isDropdownOpen && (
              <div className="absolute right-0 mt-2 w-64 bg-popover shadow-md rounded-md overflow-hidden border border-border">
                <div className="p-2 space-y-4">
                  <div>
                    <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                    Book Collections
                    </h3>
                    {allSources.map((source) => (
                      <Link
                        key={source.id}
                        href={`/hadiths?source=${source.id}`}
                        className="block px-3 py-2 text-sm rounded-md hover:bg-accent hover:text-accent-foreground"
                        onClick={() => setIsDropdownOpen(false)}
                      >
                        {source.name}
                      </Link>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </nav>

        {/* Right side items */}
        <div className="flex items-center gap-2">
          <ThemeToggle />

          {/* Mobile menu */}
          <Sheet>
            <SheetTrigger asChild>
              <Button variant="outline" size="icon" className="md:hidden">
                <Menu className="h-5 w-5" />
                <span className="sr-only">Toggle menu</span>
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-72">
              <div className="flex flex-col h-full">
                <div className="flex items-center justify-between py-2">
                  <div className="font-bold text-lg">Hadith Explorer</div>
                  <SheetClose asChild>
                    <Button variant="ghost" size="icon">
                      <X className="h-5 w-5" />
                    </Button>
                  </SheetClose>
                </div>
                
                <nav className="flex-1 py-4">
                  <div className="space-y-1">
                    {mainNavItems.map((item) => (
                      <SheetClose key={item.href} asChild>
                        <Link
                          href={item.href}
                          className={cn(
                            "flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors",
                            item.active 
                              ? "bg-accent text-accent-foreground" 
                              : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
                          )}
                        >
                          {item.icon}
                          {item.label}
                        </Link>
                      </SheetClose>
                    ))}
                  </div>

                  <div className="mt-6">
                    <h3 className="px-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                      Book Collections
                    </h3>
                    <div className="mt-2 space-y-1">
                      {allSources.map((source) => (
                        <SheetClose key={source.id} asChild>
                          <Link
                            href={`/hadiths?source=${source.id}`}
                            className="block px-3 py-2 text-sm rounded-md hover:bg-accent hover:text-accent-foreground"
                          >
                            {source.name}
                          </Link>
                        </SheetClose>
                      ))}
                    </div>
                  </div>
                </nav>

                <div className="border-t border-border py-4">
                  <div className="flex items-center justify-between">
                    <div className="text-sm">Theme</div>
                    <ThemeToggle />
                  </div>
                </div>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
}
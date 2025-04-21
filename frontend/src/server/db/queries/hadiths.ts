'use server'

import { eq, and, or, like, sql, asc } from 'drizzle-orm';
import { db } from '@/server/db';
import { hadiths, sources } from '@/server/db/schema';
import { Hadith, Source } from '@/types/hadith';

export async function getHadiths(page = 1, limit = 10) {
  const offset = (page - 1) * limit;
  
  try {
    // Use Drizzle to query existing tables
    const hadithResults = await db.select()
      .from(hadiths)
      .limit(limit)
      .offset(offset);
    
    // Count total hadiths
    const countResult = await db.select({ 
      count: sql`count(*)` 
    }).from(hadiths);
    
    const totalCount = Number(countResult[0]?.count || 0);
    
    return {
      hadiths: hadithResults as Hadith[],
      totalCount,
      page,
      limit
    };
  } catch (error) {
    console.error('Error fetching hadiths:', error);
    throw new Error('Failed to fetch hadiths');
  }
}

export async function getHadithById(id: number) {
  try {
    const result = await db.select()
      .from(hadiths)
      .where(eq(hadiths.id, id))
      .limit(1);
    
    return result[0] as Hadith || null;
  } catch (error) {
    console.error('Error fetching hadith by ID:', error);
    return null;
  }
}

export async function getHadithsBySource(sourceId: number, page = 1, limit = 10) {
  const offset = (page - 1) * limit;
  
  try {
    const hadithResults = await db.select()
      .from(hadiths)
      .where(eq(hadiths.source_id, sourceId))
      .limit(limit)
      .offset(offset);
    
    // Count total hadiths for this source
    const countResult = await db.select({ 
      count: sql`count(*)` 
    })
    .from(hadiths)
    .where(eq(hadiths.source_id, sourceId));
    
    const totalCount = Number(countResult[0]?.count || 0);
    
    return {
      hadiths: hadithResults as Hadith[],
      totalCount,
      page,
      limit
    };
  } catch (error) {
    console.error('Error fetching hadiths by source:', error);
    throw new Error('Failed to fetch hadiths by source');
  }
}

export async function getHadithsByBook(sourceId: number, book: number, page = 1, limit = 10) {
  const offset = (page - 1) * limit;
  
  try {
    const hadithResults = await db.select()
      .from(hadiths)
      .where(and(
        eq(hadiths.source_id, sourceId),
        eq(hadiths.book, book)
      ))
      .limit(limit)
      .offset(offset);
    
    // Count total hadiths for this book
    const countResult = await db.select({ 
      count: sql`count(*)` 
    })
    .from(hadiths)
    .where(and(
      eq(hadiths.source_id, sourceId),
      eq(hadiths.book, book)
    ));
    
    const totalCount = Number(countResult[0]?.count || 0);
    
    return {
      hadiths: hadithResults as Hadith[],
      totalCount,
      page,
      limit
    };
  } catch (error) {
    console.error('Error fetching hadiths by book:', error);
    throw new Error('Failed to fetch hadiths by book');
  }
}

export async function getHadithsByChapter(sourceId: number, book: number, chapter: number, page = 1, limit = 10) {
  const offset = (page - 1) * limit;
  
  try {
    const hadithResults = await db.select()
      .from(hadiths)
      .where(and(
        eq(hadiths.source_id, sourceId),
        eq(hadiths.book, book),
        eq(hadiths.chapter, chapter)
      ))
      .limit(limit)
      .offset(offset);
    
    // Count total hadiths for this chapter
    const countResult = await db.select({ 
      count: sql`count(*)` 
    })
    .from(hadiths)
    .where(and(
      eq(hadiths.source_id, sourceId),
      eq(hadiths.book, book),
      eq(hadiths.chapter, chapter)
    ));
    
    const totalCount = Number(countResult[0]?.count || 0);
    
    return {
      hadiths: hadithResults as Hadith[],
      totalCount,
      page,
      limit
    };
  } catch (error) {
    console.error('Error fetching hadiths by chapter:', error);
    throw new Error('Failed to fetch hadiths by chapter');
  }
}

export async function getSources() {
  try {
    const result = await db.select().from(sources);
    return result as Source[];
  } catch (error) {
    console.error('Error fetching sources:', error);
    throw new Error('Failed to fetch sources');
  }
}

export async function searchHadiths(query: string, page = 1, limit = 10) {
  const offset = (page - 1) * limit;
  
  try {
    // Search in english_text and arabic_text
    const hadithResults = await db.select()
      .from(hadiths)
      .where(or(
        like(hadiths.english_text, `%${query}%`),
        like(hadiths.arabic_text, `%${query}%`)
      ))
      .limit(limit)
      .offset(offset);
    
    // Count total matching hadiths
    const countResult = await db.select({ 
      count: sql`count(*)` 
    })
    .from(hadiths)
    .where(or(
      like(hadiths.english_text, `%${query}%`),
      like(hadiths.arabic_text, `%${query}%`)
    ));
    
    const totalCount = Number(countResult[0]?.count || 0);
    
    return {
      hadiths: hadithResults as Hadith[],
      totalCount,
      page,
      limit
    };
  } catch (error) {
    console.error('Error searching hadiths:', error);
    throw new Error('Failed to search hadiths');
  }
}

export async function getBooksBySource(sourceId: number) {
  try {
    // Get all book numbers from a source
    const results = await db.select({ book: hadiths.book })
      .from(hadiths)
      .where(eq(hadiths.source_id, sourceId))
      .orderBy(asc(hadiths.book));
    
    // Extract unique book numbers
    const books = [...new Set(results.map(r => r.book))];
    
    return books;
  } catch (error) {
    console.error('Error fetching books by source:', error);
    throw new Error('Failed to fetch books');
  }
}

export async function getChaptersByBook(sourceId: number, book: number) {
  try {
    // Get all chapter numbers from a book
    const results = await db.select({ chapter: hadiths.chapter })
      .from(hadiths)
      .where(and(
        eq(hadiths.source_id, sourceId),
        eq(hadiths.book, book)
      ))
      .orderBy(asc(hadiths.chapter));
    
    // Extract unique chapter numbers
    const chapters = [...new Set(results.map(r => r.chapter))];
    
    return chapters;
  } catch (error) {
    console.error('Error fetching chapters by book:', error);
    throw new Error('Failed to fetch chapters');
  }
}

// Function to search hadiths using the vector similarity endpoint
export async function searchHadithsByVector(query: string, page = 1, limit = 10) {
  try {
    // Direct API call to backend without any URL path duplication
    const baseUrl = 'http://localhost:8000';
    const endpoint = '/api/v1/search/';
    const url = new URL(endpoint, baseUrl);
    
    // Add query parameters
    url.searchParams.append('query', query);
    url.searchParams.append('page', page.toString());
    url.searchParams.append('limit', limit.toString());
    
    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
      cache: 'no-store'
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error searching hadiths by vector:', error);
    throw new Error('Failed to search hadiths by vector similarity');
  }
}

// Function to find similar hadiths
export async function findSimilarHadiths(hadithId: number, page = 1, limit = 10) {
  try {
    // Direct API call to backend without any URL path duplication
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const endpoint = `/api/v1/compare/similar-hadiths/${hadithId}`;
    const url = new URL(endpoint, baseUrl);
    
    // Add query parameters
    url.searchParams.append('page', page.toString());
    url.searchParams.append('limit', limit.toString());
    
    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
      cache: 'no-store'
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error finding similar hadiths:', error);
    throw new Error('Failed to find similar hadiths');
  }
}

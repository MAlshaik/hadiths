export type Hadith = {
  id: number;
  source_id: number;
  volume: number;
  book: number;
  chapter: number;
  number: number;
  arabic_text: string | null;
  english_text: string;
  narrator_chain: string | null;
  topics: string[] | null;
  created_at: Date;
  similarity?: number; // Optional similarity score for similar hadiths
};

export type Source = {
  id: number;
  name: string;
  tradition: string;
  description: string | null;
  compiler: string | null;
  created_at: Date;
};

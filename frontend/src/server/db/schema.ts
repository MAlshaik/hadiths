import { pgTable, serial, text, integer, timestamp } from 'drizzle-orm/pg-core';

// These are just TypeScript definitions of your existing tables
// They won't create migrations or modify your database
export const hadiths = pgTable('hadiths', {
  id: serial('id').primaryKey(),
  source_id: integer('source_id').notNull(),
  volume: integer('volume').notNull(),
  book: integer('book').notNull(),
  chapter: integer('chapter').notNull(),
  number: integer('number').notNull(),
  arabic_text: text('arabic_text'),
  english_text: text('english_text').notNull(),
  narrator_chain: text('narrator_chain'),
  topics: text('topics').array(),
  created_at: timestamp('created_at').defaultNow()
});

export const sources = pgTable('sources', {
  id: serial('id').primaryKey(),
  name: text('name').notNull(),
  tradition: text('tradition').notNull(),
  description: text('description'),
  compiler: text('compiler'),
  created_at: timestamp('created_at').defaultNow()
});

// Add your users table for future auth
export const users = pgTable('users', {
  id: serial('id').primaryKey(),
  email: text('email').notNull().unique(),
  name: text('name'),
  avatar_url: text('avatar_url'),
  created_at: timestamp('created_at').defaultNow()
});
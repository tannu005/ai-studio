import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://bqbafpkrwzkdrwvkbvsy.supabase.co';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJxYmFmcGtyd3prZHJ3dmtidnN5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkzNTQ2MDQsImV4cCI6MjA5NDkzMDYwNH0.JyegdXp4Q1rE4aHTHbNtMKEEtCESw8NeX0y4wON157Q';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://ai-studio-1-xvgm.onrender.com';

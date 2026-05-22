import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://dgbfzpqenfhsygbmgfuy.supabase.co'
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRnYmZ6cHFlbmZoc3lnYm1nZnV5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc5MTU1MTgsImV4cCI6MjA5MzQ5MTUxOH0.WdVQfgn0R5X4VMrSZDpTCePema6IUxJIhVaJBL8iRZs'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

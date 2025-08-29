import { useState } from 'react';

const API_KEY = import.meta.env.VITE_GEMINI_API_KEY;
const API_URL = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=${API_KEY}`;

export const useGemini = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const generateContent = async (prompt) => {
    setLoading(true);
    setError(null);
    
    if (!API_KEY) {
      setError('API key is not configured.');
      setLoading(false);
      return 'Error: API key not found. Please set VITE_GEMINI_API_KEY in your .env file.';
    }
    
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }] })
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      const data = await response.json();
      return data.candidates[0].content.parts[0].text;
    } catch (err) {
      setError(err.message);
      return 'Sorry, an error occurred while generating a response.';
    } finally {
      setLoading(false);
    }
  };

  return { generateContent, loading, error };
};




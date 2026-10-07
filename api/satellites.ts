/**
 * Vercel Serverless Function: /api/satellites
 * 
 * Proxies CelesTrak TLE data.
 * CelesTrak is keyless but may have rate limits.
 */

import type { VercelRequest, VercelResponse } from '@vercel/node';

const CELESTRAK_URL = 'https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle';

let cache: { data: string; timestamp: number } | null = null;
const CACHE_TTL = 300000; // 5 minutes

export default async function handler(req: VercelRequest, res: VercelResponse) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    if (cache && Date.now() - cache.timestamp < CACHE_TTL) {
      return res.status(200).json({
        tle: cache.data,
        cached: true,
        cachedAt: new Date(cache.timestamp).toISOString(),
      });
    }

    const response = await fetch(CELESTRAK_URL, {
      headers: {
        'User-Agent': 'GOD-EYE-SAE/2.0',
      },
    });

    if (!response.ok) {
      throw new Error(`CelesTrak returned ${response.status}`);
    }

    const data = await response.text();
    cache = { data, timestamp: Date.now() };

    return res.status(200).json({
      tle: data,
      source: 'CelesTrak',
      retrievedAt: new Date().toISOString(),
      cached: false,
    });
  } catch (error) {
    console.error('Satellite API error:', error);
    return res.status(500).json({
      error: 'Failed to fetch satellite data',
      message: error instanceof Error ? error.message : 'Unknown error',
    });
  }
}

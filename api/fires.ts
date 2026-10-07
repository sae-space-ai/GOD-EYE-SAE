/**
 * Vercel Serverless Function: /api/fires
 * 
 * Proxies NASA FIRMS fire detection data.
 * Requires FIRMS_MAP_KEY environment variable (server-side only).
 * 
 * IMPORTANT: Never expose FIRMS_MAP_KEY to the client.
 */

import type { VercelRequest, VercelResponse } from '@vercel/node';

const FIRMS_API_URL = 'https://firms.modaps.eosdis.nasa.gov/api/area/csv';

let cache: { data: string; timestamp: number } | null = null;
const CACHE_TTL = 180000; // 3 minutes

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

  // Check if FIRMS key is configured
  const firmsKey = process.env.FIRMS_MAP_KEY;
  if (!firmsKey) {
    return res.status(503).json({
      error: 'NASA FIRMS not configured',
      message: 'FIRMS_MAP_KEY environment variable is required',
      configured: false,
    });
  }

  try {
    // Default to global bbox if not specified
    const { bbox = '-180,-90,180,90', source = 'VIIRS_SNPP_NRT', days = '1' } = req.query;

    const cacheKey = `${bbox}_${source}_${days}`;
    if (cache && Date.now() - cache.timestamp < CACHE_TTL) {
      return res.status(200).json({
        data: cache.data,
        cached: true,
        cachedAt: new Date(cache.timestamp).toISOString(),
      });
    }

    const url = `${FIRMS_API_URL}/${source}/${bbox}/${days}`;

    const response = await fetch(url, {
      headers: {
        'MAP_KEY': firmsKey,
        'User-Agent': 'GOD-EYE-SAE/2.0',
      },
    });

    if (!response.ok) {
      throw new Error(`FIRMS API returned ${response.status}`);
    }

    const data = await response.text();
    cache = { data, timestamp: Date.now() };

    return res.status(200).json({
      data,
      source: 'NASA FIRMS',
      sourceType: source,
      retrievedAt: new Date().toISOString(),
      cached: false,
    });
  } catch (error) {
    console.error('FIRMS API error:', error);
    return res.status(500).json({
      error: 'Failed to fetch fire data',
      message: error instanceof Error ? error.message : 'Unknown error',
    });
  }
}

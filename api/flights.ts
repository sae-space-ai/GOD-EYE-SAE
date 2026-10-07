/**
 * Vercel Serverless Function: /api/flights
 * 
 * Proxies OpenSky Network aircraft data.
 * OpenSky anonymous access has rate limits.
 */

import type { VercelRequest, VercelResponse } from '@vercel/node';

const OPENSKY_URL = 'https://opensky-network.org/api/states/all';

let cache: { data: any; timestamp: number } | null = null;
const CACHE_TTL = 15000; // 15 seconds (respect OpenSky rate limits)

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
        ...cache.data,
        cached: true,
        cachedAt: new Date(cache.timestamp).toISOString(),
      });
    }

    const response = await fetch(OPENSKY_URL, {
      headers: {
        'Accept': 'application/json',
        'User-Agent': 'GOD-EYE-SAE/2.0',
      },
    });

    if (!response.ok) {
      if (response.status === 429) {
        return res.status(429).json({
          error: 'OpenSky rate limit exceeded',
          message: 'Please wait before requesting again',
        });
      }
      throw new Error(`OpenSky returned ${response.status}`);
    }

    const data = await response.json();
    cache = { data, timestamp: Date.now() };

    return res.status(200).json({
      ...data,
      source: 'OpenSky Network',
      retrievedAt: new Date().toISOString(),
      cached: false,
    });
  } catch (error) {
    console.error('Flight API error:', error);
    return res.status(500).json({
      error: 'Failed to fetch flight data',
      message: error instanceof Error ? error.message : 'Unknown error',
    });
  }
}

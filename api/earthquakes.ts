/**
 * Vercel Serverless Function: /api/earthquakes
 * 
 * Proxies USGS earthquake data with caching.
 * USGS API is keyless and CORS-enabled, but this endpoint
 * provides normalization and caching for the frontend.
 */

import type { VercelRequest, VercelResponse } from '@vercel/node';

const USGS_API_URL = 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson';

// Simple in-memory cache (Vercel Functions are stateless, but this helps within a single invocation)
let cache: { data: any; timestamp: number } | null = null;
const CACHE_TTL = 60000; // 1 minute

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // CORS headers
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
    // Check cache
    if (cache && Date.now() - cache.timestamp < CACHE_TTL) {
      return res.status(200).json({
        ...cache.data,
        cached: true,
        cachedAt: new Date(cache.timestamp).toISOString(),
      });
    }

    // Fetch from USGS
    const response = await fetch(USGS_API_URL, {
      headers: {
        'User-Agent': 'GOD-EYE-SAE/2.0',
      },
    });

    if (!response.ok) {
      throw new Error(`USGS API returned ${response.status}`);
    }

    const data = await response.json();

    // Update cache
    cache = { data, timestamp: Date.now() };

    // Return normalized response
    return res.status(200).json({
      ...data,
      source: 'USGS Earthquake Hazards Program',
      retrievedAt: new Date().toISOString(),
      cached: false,
    });
  } catch (error) {
    console.error('Earthquake API error:', error);
    return res.status(500).json({
      error: 'Failed to fetch earthquake data',
      message: error instanceof Error ? error.message : 'Unknown error',
    });
  }
}

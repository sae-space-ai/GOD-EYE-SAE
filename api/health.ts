/**
 * Vercel Serverless Function: /api/health
 * 
 * Returns system health status.
 * Compatible with Vercel Functions runtime.
 */

import type { VercelRequest, VercelResponse } from '@vercel/node';

export default function handler(req: VercelRequest, res: VercelResponse) {
  const health = {
    status: 'operational',
    version: '2.0.0',
    timestamp: new Date().toISOString(),
    environment: process.env.NODE_ENV || 'development',
    services: {
      frontend: 'operational',
      cesium: 'operational',
      usgs: 'operational',
      celestrak: 'operational',
      opensky: 'operational',
      nasaFirms: process.env.FIRMS_MAP_KEY ? 'configured' : 'not_configured',
      aisstream: process.env.AISSTREAM_API_KEY ? 'configured' : 'not_configured',
    },
  };

  res.status(200).json(health);
}

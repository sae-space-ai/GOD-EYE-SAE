import { useEffect, useRef, useCallback } from 'react';
import * as THREE from 'three';

interface GlobeProps {
  className?: string;
  onCoordinateChange?: (lat: number, lng: number) => void;
}

export default function Globe({ className = '', onCoordinateChange }: GlobeProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const globeRef = useRef<THREE.Mesh | null>(null);
  const atmosphereRef = useRef<THREE.Mesh | null>(null);
  const frameRef = useRef<number>(0);
  const isDragging = useRef(false);
  const previousMouse = useRef({ x: 0, y: 0 });
  const rotationVelocity = useRef({ x: 0, y: 0 });
  const targetRotation = useRef({ x: 0.3, y: 0 });

  const createGlobe = useCallback(() => {
    if (!containerRef.current) return;

    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight;

    // Scene
    const scene = new THREE.Scene();
    sceneRef.current = scene;

    // Camera
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.z = 3.5;
    cameraRef.current = camera;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ 
      antialias: true, 
      alpha: true,
      powerPreference: 'high-performance'
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0);
    containerRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Globe geometry
    const geometry = new THREE.SphereGeometry(1, 64, 64);
    
    // Create earth texture procedurally
    const canvas = document.createElement('canvas');
    canvas.width = 2048;
    canvas.height = 1024;
    const ctx = canvas.getContext('2d')!;
    
    // Ocean base
    const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
    gradient.addColorStop(0, '#0a1628');
    gradient.addColorStop(0.3, '#0d1f3c');
    gradient.addColorStop(0.5, '#0f2847');
    gradient.addColorStop(0.7, '#0d1f3c');
    gradient.addColorStop(1, '#0a1628');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw simplified continents
    ctx.fillStyle = '#1a3a5c';
    ctx.strokeStyle = '#00d4ff33';
    ctx.lineWidth = 1;

    // Grid lines
    ctx.strokeStyle = '#00d4ff15';
    ctx.lineWidth = 0.5;
    for (let i = 0; i < 36; i++) {
      ctx.beginPath();
      ctx.moveTo(i * (canvas.width / 36), 0);
      ctx.lineTo(i * (canvas.width / 36), canvas.height);
      ctx.stroke();
    }
    for (let i = 0; i < 18; i++) {
      ctx.beginPath();
      ctx.moveTo(0, i * (canvas.height / 18));
      ctx.lineTo(canvas.width, i * (canvas.height / 18));
      ctx.stroke();
    }

    // Simplified continent shapes
    const drawContinent = (points: [number, number][]) => {
      ctx.beginPath();
      ctx.moveTo(points[0][0], points[0][1]);
      for (let i = 1; i < points.length; i++) {
        ctx.lineTo(points[i][0], points[i][1]);
      }
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    };

    ctx.fillStyle = '#1a4a3a';
    ctx.strokeStyle = '#00d4ff44';
    ctx.lineWidth = 1.5;

    // North America
    drawContinent([
      [200, 200], [350, 180], [420, 220], [450, 300], [400, 380],
      [350, 420], [280, 400], [220, 350], [180, 280], [200, 200]
    ]);

    // South America
    drawContinent([
      [350, 450], [400, 440], [430, 500], [420, 600], [380, 700],
      [340, 750], [310, 700], [300, 600], [320, 500], [350, 450]
    ]);

    // Europe
    drawContinent([
      [900, 200], [1000, 180], [1050, 200], [1080, 250], [1050, 300],
      [980, 320], [920, 300], [880, 260], [900, 200]
    ]);

    // Africa
    drawContinent([
      [900, 350], [1000, 340], [1080, 400], [1100, 500], [1050, 620],
      [980, 680], [920, 650], [880, 550], [870, 450], [900, 350]
    ]);

    // Asia
    drawContinent([
      [1100, 180], [1300, 150], [1500, 180], [1600, 250], [1650, 350],
      [1600, 420], [1450, 450], [1300, 400], [1150, 350], [1100, 280], [1100, 180]
    ]);

    // Australia
    drawContinent([
      [1500, 550], [1600, 530], [1680, 570], [1700, 630], [1650, 680],
      [1550, 690], [1480, 650], [1470, 590], [1500, 550]
    ]);

    // Data points (simulated active locations)
    const dataPoints = [
      { x: 350, y: 300, color: '#00ff88' },  // Americas
      { x: 950, y: 270, color: '#00d4ff' },   // Europe
      { x: 1000, y: 450, color: '#ff6b35' },  // Africa
      { x: 1400, y: 300, color: '#00d4ff' },  // Asia
      { x: 1580, y: 600, color: '#00ff88' },  // Australia
      { x: 380, y: 550, color: '#ffcc00' },   // South America
    ];

    dataPoints.forEach(point => {
      ctx.beginPath();
      ctx.arc(point.x, point.y, 4, 0, Math.PI * 2);
      ctx.fillStyle = point.color;
      ctx.fill();
      
      // Glow effect
      ctx.beginPath();
      ctx.arc(point.x, point.y, 8, 0, Math.PI * 2);
      ctx.fillStyle = point.color + '33';
      ctx.fill();
    });

    const texture = new THREE.CanvasTexture(canvas);
    texture.needsUpdate = true;

    // Globe material
    const material = new THREE.MeshPhongMaterial({
      map: texture,
      specular: new THREE.Color(0x00d4ff),
      shininess: 15,
      transparent: true,
      opacity: 0.95,
    });

    const globe = new THREE.Mesh(geometry, material);
    scene.add(globe);
    globeRef.current = globe;

    // Atmosphere glow
    const atmosphereGeometry = new THREE.SphereGeometry(1.05, 64, 64);
    const atmosphereMaterial = new THREE.MeshPhongMaterial({
      color: 0x00d4ff,
      transparent: true,
      opacity: 0.08,
      side: THREE.BackSide,
    });
    const atmosphere = new THREE.Mesh(atmosphereGeometry, atmosphereMaterial);
    scene.add(atmosphere);
    atmosphereRef.current = atmosphere;

    // Outer glow
    const outerGlowGeometry = new THREE.SphereGeometry(1.15, 32, 32);
    const outerGlowMaterial = new THREE.MeshBasicMaterial({
      color: 0x00d4ff,
      transparent: true,
      opacity: 0.03,
      side: THREE.BackSide,
    });
    const outerGlow = new THREE.Mesh(outerGlowGeometry, outerGlowMaterial);
    scene.add(outerGlow);

    // Lights
    const ambientLight = new THREE.AmbientLight(0x404060, 0.6);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 1.0);
    directionalLight.position.set(5, 3, 5);
    scene.add(directionalLight);

    const rimLight = new THREE.DirectionalLight(0x00d4ff, 0.3);
    rimLight.position.set(-3, -1, -3);
    scene.add(rimLight);

    // Stars
    const starsGeometry = new THREE.BufferGeometry();
    const starsCount = 2000;
    const positions = new Float32Array(starsCount * 3);
    for (let i = 0; i < starsCount * 3; i += 3) {
      const radius = 50 + Math.random() * 100;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      positions[i] = radius * Math.sin(phi) * Math.cos(theta);
      positions[i + 1] = radius * Math.sin(phi) * Math.sin(theta);
      positions[i + 2] = radius * Math.cos(phi);
    }
    starsGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const starsMaterial = new THREE.PointsMaterial({
      color: 0xffffff,
      size: 0.1,
      transparent: true,
      opacity: 0.6,
    });
    const stars = new THREE.Points(starsGeometry, starsMaterial);
    scene.add(stars);

    // Animation loop
    const animate = () => {
      frameRef.current = requestAnimationFrame(animate);

      if (globe) {
        if (!isDragging.current) {
          // Auto-rotation
          targetRotation.current.y += 0.001;
          // Apply velocity damping
          rotationVelocity.current.x *= 0.95;
          rotationVelocity.current.y *= 0.95;
          targetRotation.current.x += rotationVelocity.current.x;
          targetRotation.current.y += rotationVelocity.current.y;
        }

        globe.rotation.x += (targetRotation.current.x - globe.rotation.x) * 0.1;
        globe.rotation.y += (targetRotation.current.y - globe.rotation.y) * 0.1;
        
        if (atmosphere) {
          atmosphere.rotation.copy(globe.rotation);
        }
      }

      renderer.render(scene, camera);
    };
    animate();

    // Report initial coordinates
    if (onCoordinateChange) {
      onCoordinateChange(0, 0);
    }
  }, [onCoordinateChange]);

  useEffect(() => {
    createGlobe();

    const handleResize = () => {
      if (!containerRef.current || !rendererRef.current || !cameraRef.current) return;
      const width = containerRef.current.clientWidth;
      const height = containerRef.current.clientHeight;
      rendererRef.current.setSize(width, height);
      cameraRef.current.aspect = width / height;
      cameraRef.current.updateProjectionMatrix();
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (frameRef.current) cancelAnimationFrame(frameRef.current);
      if (rendererRef.current && containerRef.current) {
        containerRef.current.removeChild(rendererRef.current.domElement);
        rendererRef.current.dispose();
      }
    };
  }, [createGlobe]);

  const handleMouseDown = (e: React.MouseEvent) => {
    isDragging.current = true;
    previousMouse.current = { x: e.clientX, y: e.clientY };
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging.current) return;
    const deltaX = e.clientX - previousMouse.current.x;
    const deltaY = e.clientY - previousMouse.current.y;
    
    targetRotation.current.y += deltaX * 0.005;
    targetRotation.current.x += deltaY * 0.005;
    targetRotation.current.x = Math.max(-Math.PI / 2, Math.min(Math.PI / 2, targetRotation.current.x));
    
    rotationVelocity.current = { x: deltaY * 0.001, y: deltaX * 0.001 };
    previousMouse.current = { x: e.clientX, y: e.clientY };

    // Calculate approximate coordinates
    if (onCoordinateChange && globeRef.current) {
      const lat = -(targetRotation.current.x * 180) / Math.PI;
      const lng = ((targetRotation.current.y * 180) / Math.PI) % 360;
      onCoordinateChange(
        Math.round(lat * 100) / 100,
        Math.round(lng * 100) / 100
      );
    }
  };

  const handleMouseUp = () => {
    isDragging.current = false;
  };

  const handleWheel = (e: React.WheelEvent) => {
    if (!cameraRef.current) return;
    cameraRef.current.position.z += e.deltaY * 0.002;
    cameraRef.current.position.z = Math.max(2, Math.min(8, cameraRef.current.position.z));
  };

  return (
    <div
      ref={containerRef}
      className={`w-full h-full cursor-grab active:cursor-grabbing ${className}`}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      onWheel={handleWheel}
      role="application"
      aria-label="Globo 3D interactivo"
    />
  );
}

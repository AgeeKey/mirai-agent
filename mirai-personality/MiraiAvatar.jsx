import React, { useState, useEffect, useRef } from 'react';
import * as THREE from 'three';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { useGLTF, Text, Html, Environment, PerspectiveCamera } from '@react-three/drei';
import { animated, useSpring, config } from '@react-spring/three';

// Emotion states for Mirai's expressions
const EMOTIONS = {
  HAPPY: {
    eyeBrows: 0.2,
    eyesSize: 1.1,
    mouthCurve: 0.8,
    blush: 0.6,
    energy: 0.8,
    color: '#FFB6C1'
  },
  EXCITED: {
    eyeBrows: 0.4,
    eyesSize: 1.3,
    mouthCurve: 1.0,
    blush: 0.8,
    energy: 1.0,
    color: '#FF69B4'
  },
  CURIOUS: {
    eyeBrows: 0.3,
    eyesSize: 1.2,
    mouthCurve: 0.2,
    blush: 0.3,
    energy: 0.6,
    color: '#DDA0DD'
  },
  CALM: {
    eyeBrows: 0.0,
    eyesSize: 0.9,
    mouthCurve: 0.3,
    blush: 0.2,
    energy: 0.3,
    color: '#B0E0E6'
  },
  PLAYFUL: {
    eyeBrows: 0.1,
    eyesSize: 1.1,
    mouthCurve: 0.7,
    blush: 0.5,
    energy: 0.9,
    color: '#FFD700'
  },
  THOUGHTFUL: {
    eyeBrows: -0.1,
    eyesSize: 0.8,
    mouthCurve: 0.1,
    blush: 0.1,
    energy: 0.4,
    color: '#9370DB'
  },
  AFFECTIONATE: {
    eyeBrows: 0.1,
    eyesSize: 1.0,
    mouthCurve: 0.6,
    blush: 0.9,
    energy: 0.7,
    color: '#FF1493'
  }
};

// Mirai's personality traits
const PERSONALITY = {
  traits: {
    openness: 0.9,
    conscientiousness: 0.7,
    extraversion: 0.8,
    agreeableness: 0.9,
    neuroticism: 0.3
  },
  archetype: 'genki_girl',
  likes: ['trading', 'anime', 'music', 'helping friends', 'learning'],
  dislikes: ['being ignored', 'sad friends', 'market crashes'],
  speech: {
    formalityLevel: 0.3,
    useEmoji: true,
    japanesePhrases: true,
    enthusiasm: 0.8
  }
};

// Main Mirai Avatar Component
function MiraiAvatar({ emotion = 'HAPPY', isListening = false, isSpeaking = false, lookAt = null }) {
  const meshRef = useRef();
  const { scene, camera, gl } = useThree();
  
  // Current emotion state
  const currentEmotion = EMOTIONS[emotion] || EMOTIONS.HAPPY;
  
  // Animated properties based on emotion
  const { eyeBrows, eyesSize, mouthCurve, blush, energy } = useSpring({
    eyeBrows: currentEmotion.eyeBrows,
    eyesSize: currentEmotion.eyesSize,
    mouthCurve: currentEmotion.mouthCurve,
    blush: currentEmotion.blush,
    energy: currentEmotion.energy,
    config: config.gentle
  });

  // Breathing and idle animations
  const { scale, positionY } = useSpring({
    scale: energy.to(e => 0.95 + e * 0.05),
    positionY: energy.to(e => Math.sin(Date.now() * 0.002) * 0.02 * e),
    config: { tension: 100, friction: 50 }
  });

  // Look-at behavior
  useFrame((state, delta) => {
    if (meshRef.current && lookAt) {
      const targetPosition = new THREE.Vector3(...lookAt);
      meshRef.current.lookAt(targetPosition);
    }
    
    // Idle head movement
    if (meshRef.current && !lookAt) {
      meshRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.5) * 0.1;
      meshRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.3) * 0.05;
    }
  });

  return (
    <animated.group ref={meshRef} scale={scale} position-y={positionY}>
      {/* Head */}
      <MiraiHead 
        emotion={currentEmotion}
        eyeBrows={eyeBrows}
        eyesSize={eyesSize}
        mouthCurve={mouthCurve}
        blush={blush}
        isSpeaking={isSpeaking}
      />
      
      {/* Hair */}
      <MiraiHair emotion={currentEmotion} energy={energy} />
      
      {/* Body */}
      <MiraiBody emotion={currentEmotion} />
      
      {/* Clothing */}
      <MiraiOutfit emotion={currentEmotion} />
      
      {/* Special effects */}
      {isListening && <ListeningEffect />}
      {isSpeaking && <SpeakingEffect />}
    </animated.group>
  );
}

// Mirai's head with facial expressions
function MiraiHead({ emotion, eyeBrows, eyesSize, mouthCurve, blush, isSpeaking }) {
  const headRef = useRef();
  
  // Lip sync animation when speaking
  const { mouthOpen } = useSpring({
    mouthOpen: isSpeaking ? Math.sin(Date.now() * 0.02) * 0.3 + 0.3 : 0,
    config: { tension: 200, friction: 20 }
  });

  return (
    <group ref={headRef} position={[0, 1.6, 0]}>
      {/* Face base */}
      <mesh position={[0, 0, 0.1]}>
        <sphereGeometry args={[0.4, 32, 32]} />
        <meshStandardMaterial 
          color="#FFEBD7" 
          roughness={0.3}
          metalness={0.1}
        />
      </mesh>
      
      {/* Eyes */}
      <animated.group scale={eyesSize}>
        {/* Left eye */}
        <mesh position={[-0.15, 0.1, 0.35]}>
          <sphereGeometry args={[0.08, 16, 16]} />
          <meshStandardMaterial color="#4169E1" />
        </mesh>
        
        {/* Right eye */}
        <mesh position={[0.15, 0.1, 0.35]}>
          <sphereGeometry args={[0.08, 16, 16]} />
          <meshStandardMaterial color="#4169E1" />
        </mesh>
        
        {/* Eye highlights */}
        <mesh position={[-0.13, 0.12, 0.4]}>
          <sphereGeometry args={[0.02, 8, 8]} />
          <meshStandardMaterial color="white" />
        </mesh>
        <mesh position={[0.17, 0.12, 0.4]}>
          <sphereGeometry args={[0.02, 8, 8]} />
          <meshStandardMaterial color="white" />
        </mesh>
      </animated.group>
      
      {/* Eyebrows */}
      <animated.group position-y={eyeBrows.to(e => 0.2 + e * 0.1)}>
        <mesh position={[-0.15, 0.25, 0.35]} rotation={[0, 0, 0.2]}>
          <cylinderGeometry args={[0.02, 0.02, 0.15]} />
          <meshStandardMaterial color="#8B4513" />
        </mesh>
        <mesh position={[0.15, 0.25, 0.35]} rotation={[0, 0, -0.2]}>
          <cylinderGeometry args={[0.02, 0.02, 0.15]} />
          <meshStandardMaterial color="#8B4513" />
        </mesh>
      </animated.group>
      
      {/* Mouth */}
      <animated.mesh 
        position={[0, -0.1, 0.35]}
        scale-y={mouthCurve.to(curve => 0.5 + curve * 0.5)}
        scale-x={mouthOpen.to(open => 1 + open * 0.5)}
      >
        <sphereGeometry args={[0.06, 16, 8]} />
        <meshStandardMaterial color="#FF69B4" />
      </animated.mesh>
      
      {/* Blush */}
      <animated.group scale={blush.to(b => b)}>
        <mesh position={[-0.25, 0, 0.3]}>
          <sphereGeometry args={[0.04, 16, 16]} />
          <meshStandardMaterial 
            color="#FFB6C1" 
            transparent 
            opacity={0.6}
          />
        </mesh>
        <mesh position={[0.25, 0, 0.3]}>
          <sphereGeometry args={[0.04, 16, 16]} />
          <meshStandardMaterial 
            color="#FFB6C1" 
            transparent 
            opacity={0.6}
          />
        </mesh>
      </animated.group>
      
      {/* Nose */}
      <mesh position={[0, 0.05, 0.38]}>
        <sphereGeometry args={[0.015, 8, 8]} />
        <meshStandardMaterial color="#FFEBD7" />
      </mesh>
    </group>
  );
}

// Mirai's hair with physics
function MiraiHair({ emotion, energy }) {
  const hairRef = useRef();
  
  // Hair movement based on energy level
  const { sway } = useSpring({
    sway: energy.to(e => Math.sin(Date.now() * 0.003) * e * 0.05),
    config: { tension: 80, friction: 40 }
  });

  return (
    <animated.group ref={hairRef} rotation-z={sway}>
      {/* Main hair volume */}
      <mesh position={[0, 1.8, -0.1]}>
        <sphereGeometry args={[0.5, 16, 16]} />
        <meshStandardMaterial color="#FF1493" roughness={0.8} />
      </mesh>
      
      {/* Hair strands */}
      {Array.from({ length: 8 }, (_, i) => (
        <mesh 
          key={i}
          position={[
            (Math.random() - 0.5) * 0.8,
            1.4 + Math.random() * 0.4,
            -0.3 + Math.random() * 0.2
          ]}
          rotation={[
            Math.random() * 0.3,
            Math.random() * Math.PI * 2,
            Math.random() * 0.3
          ]}
        >
          <cylinderGeometry args={[0.02, 0.01, 0.3]} />
          <meshStandardMaterial color="#FF1493" />
        </mesh>
      ))}
      
      {/* Twintails */}
      <group>
        {/* Left twintail */}
        <mesh position={[-0.4, 1.5, -0.2]}>
          <cylinderGeometry args={[0.1, 0.05, 0.6]} />
          <meshStandardMaterial color="#FF1493" />
        </mesh>
        
        {/* Right twintail */}
        <mesh position={[0.4, 1.5, -0.2]}>
          <cylinderGeometry args={[0.1, 0.05, 0.6]} />
          <meshStandardMaterial color="#FF1493" />
        </mesh>
      </group>
    </animated.group>
  );
}

// Mirai's body
function MiraiBody({ emotion }) {
  return (
    <group>
      {/* Torso */}
      <mesh position={[0, 0.8, 0]}>
        <cylinderGeometry args={[0.25, 0.2, 0.8]} />
        <meshStandardMaterial color="#FFEBD7" />
      </mesh>
      
      {/* Arms */}
      <mesh position={[-0.4, 0.8, 0]}>
        <cylinderGeometry args={[0.08, 0.06, 0.6]} />
        <meshStandardMaterial color="#FFEBD7" />
      </mesh>
      <mesh position={[0.4, 0.8, 0]}>
        <cylinderGeometry args={[0.08, 0.06, 0.6]} />
        <meshStandardMaterial color="#FFEBD7" />
      </mesh>
      
      {/* Hands */}
      <mesh position={[-0.4, 0.4, 0]}>
        <sphereGeometry args={[0.08, 16, 16]} />
        <meshStandardMaterial color="#FFEBD7" />
      </mesh>
      <mesh position={[0.4, 0.4, 0]}>
        <sphereGeometry args={[0.08, 16, 16]} />
        <meshStandardMaterial color="#FFEBD7" />
      </mesh>
    </group>
  );
}

// Mirai's outfit
function MiraiOutfit({ emotion }) {
  return (
    <group>
      {/* School uniform top */}
      <mesh position={[0, 0.9, 0.05]}>
        <cylinderGeometry args={[0.27, 0.22, 0.6]} />
        <meshStandardMaterial color="#4169E1" />
      </mesh>
      
      {/* Collar */}
      <mesh position={[0, 1.15, 0.15]}>
        <boxGeometry args={[0.4, 0.1, 0.05]} />
        <meshStandardMaterial color="white" />
      </mesh>
      
      {/* Tie */}
      <mesh position={[0, 1.0, 0.2]}>
        <boxGeometry args={[0.08, 0.3, 0.02]} />
        <meshStandardMaterial color="#FF1493" />
      </mesh>
      
      {/* Skirt */}
      <mesh position={[0, 0.3, 0]}>
        <cylinderGeometry args={[0.35, 0.25, 0.3]} />
        <meshStandardMaterial color="#FF1493" />
      </mesh>
      
      {/* Legs */}
      <mesh position={[-0.1, -0.2, 0]}>
        <cylinderGeometry args={[0.08, 0.06, 0.6]} />
        <meshStandardMaterial color="#FFEBD7" />
      </mesh>
      <mesh position={[0.1, -0.2, 0]}>
        <cylinderGeometry args={[0.08, 0.06, 0.6]} />
        <meshStandardMaterial color="#FFEBD7" />
      </mesh>
      
      {/* Shoes */}
      <mesh position={[-0.1, -0.6, 0.1]}>
        <boxGeometry args={[0.12, 0.08, 0.25]} />
        <meshStandardMaterial color="#8B4513" />
      </mesh>
      <mesh position={[0.1, -0.6, 0.1]}>
        <boxGeometry args={[0.12, 0.08, 0.25]} />
        <meshStandardMaterial color="#8B4513" />
      </mesh>
    </group>
  );
}

// Visual effect when Mirai is listening
function ListeningEffect() {
  const particlesRef = useRef();
  
  useFrame((state) => {
    if (particlesRef.current) {
      particlesRef.current.rotation.y += 0.01;
    }
  });

  return (
    <group ref={particlesRef} position={[0, 2.2, 0]}>
      {Array.from({ length: 12 }, (_, i) => (
        <mesh 
          key={i}
          position={[
            Math.cos(i * Math.PI * 2 / 12) * 0.6,
            Math.sin(Date.now() * 0.005 + i) * 0.1,
            Math.sin(i * Math.PI * 2 / 12) * 0.6
          ]}
        >
          <sphereGeometry args={[0.02, 8, 8]} />
          <meshStandardMaterial 
            color="#00FFFF" 
            emissive="#00FFFF"
            emissiveIntensity={0.3}
          />
        </mesh>
      ))}
    </group>
  );
}

// Visual effect when Mirai is speaking
function SpeakingEffect() {
  const waveRef = useRef();
  
  useFrame((state) => {
    if (waveRef.current) {
      waveRef.current.scale.setScalar(1 + Math.sin(state.clock.elapsedTime * 5) * 0.1);
    }
  });

  return (
    <group ref={waveRef} position={[0, 1.6, 0.5]}>
      {Array.from({ length: 5 }, (_, i) => (
        <mesh 
          key={i}
          position={[
            (i - 2) * 0.1,
            0,
            0
          ]}
          scale={[1, Math.sin(Date.now() * 0.01 + i) * 0.5 + 1, 1]}
        >
          <boxGeometry args={[0.02, 0.1, 0.02]} />
          <meshStandardMaterial 
            color="#FF69B4" 
            emissive="#FF69B4"
            emissiveIntensity={0.2}
          />
        </mesh>
      ))}
    </group>
  );
}

// Environment and lighting
function MiraiEnvironment() {
  return (
    <>
      {/* Ambient lighting */}
      <ambientLight intensity={0.4} color="#FFE4E1" />
      
      {/* Main directional light */}
      <directionalLight
        position={[5, 10, 5]}
        intensity={0.8}
        color="#FFFFFF"
        castShadow
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
      />
      
      {/* Fill light */}
      <pointLight
        position={[-3, 5, 3]}
        intensity={0.3}
        color="#FFB6C1"
      />
      
      {/* Rim light */}
      <pointLight
        position={[0, 2, -3]}
        intensity={0.2}
        color="#DDA0DD"
      />
      
      {/* Environment background */}
      <Environment preset="sunset" />
    </>
  );
}

// Particle effects for magic/sparkles
function MagicParticles() {
  const particlesRef = useRef();
  const particleCount = 50;
  
  useFrame((state) => {
    if (particlesRef.current) {
      particlesRef.current.rotation.y += 0.002;
    }
  });

  return (
    <group ref={particlesRef}>
      {Array.from({ length: particleCount }, (_, i) => (
        <mesh 
          key={i}
          position={[
            (Math.random() - 0.5) * 10,
            Math.random() * 8,
            (Math.random() - 0.5) * 10
          ]}
        >
          <sphereGeometry args={[0.01, 8, 8]} />
          <meshStandardMaterial 
            color={`hsl(${Math.random() * 60 + 300}, 100%, 75%)`}
            emissive={`hsl(${Math.random() * 60 + 300}, 100%, 50%)`}
            emissiveIntensity={0.5}
          />
        </mesh>
      ))}
    </group>
  );
}

// Main component
export default function MiraiAvatarSystem({ 
  emotion = 'HAPPY', 
  isListening = false, 
  isSpeaking = false,
  showParticles = true,
  cameraPosition = [0, 1.5, 3],
  onInteraction = () => {}
}) {
  const [mousePosition, setMousePosition] = useState([0, 0, 0]);
  const [isHovered, setIsHovered] = useState(false);

  // Track mouse for look-at behavior
  const handleMouseMove = (event) => {
    const x = (event.clientX / window.innerWidth) * 2 - 1;
    const y = -(event.clientY / window.innerHeight) * 2 + 1;
    setMousePosition([x * 2, y * 2 + 1.5, 2]);
  };

  useEffect(() => {
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <div 
      style={{ 
        width: '100%', 
        height: '100vh', 
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        cursor: isHovered ? 'pointer' : 'default'
      }}
      onClick={onInteraction}
    >
      <Canvas shadows camera={{ position: cameraPosition, fov: 50 }}>
        <MiraiEnvironment />
        
        <MiraiAvatar
          emotion={emotion}
          isListening={isListening}
          isSpeaking={isSpeaking}
          lookAt={mousePosition}
        />
        
        {showParticles && <MagicParticles />}
        
        {/* Interactive area */}
        <mesh
          position={[0, 1, 0]}
          onPointerEnter={() => setIsHovered(true)}
          onPointerLeave={() => setIsHovered(false)}
          visible={false}
        >
          <boxGeometry args={[2, 3, 2]} />
        </mesh>
      </Canvas>
      
      {/* UI overlay */}
      <div style={{
        position: 'absolute',
        bottom: '20px',
        left: '20px',
        color: 'white',
        fontFamily: 'Arial, sans-serif',
        fontSize: '14px',
        background: 'rgba(0,0,0,0.5)',
        padding: '10px',
        borderRadius: '10px'
      }}>
        <div>Emotion: {emotion}</div>
        <div>Listening: {isListening ? 'Yes' : 'No'}</div>
        <div>Speaking: {isSpeaking ? 'Yes' : 'No'}</div>
      </div>
    </div>
  );
}
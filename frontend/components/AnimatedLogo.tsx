'use client';

import { useRef, useState, useEffect } from 'react';

interface AnimatedLogoProps {
  className?: string;
  onAnimationComplete?: () => void;
}

const SESSION_KEY = 'logoAnimationPlayed';

export default function AnimatedLogo({ className = '', onAnimationComplete }: AnimatedLogoProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const [showStatic, setShowStatic] = useState(false);
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);

    // Check if animation already played this session
    const hasPlayed = sessionStorage.getItem(SESSION_KEY) === 'true';
    if (hasPlayed) {
      setShowStatic(true);
      return;
    }

    // Play video and audio together
    const video = videoRef.current;
    const audio = audioRef.current;

    if (video) {
      video.play().catch(() => {
        // Autoplay blocked, show static
        setShowStatic(true);
      });
    }

    if (audio) {
      // Try to play audio (may be blocked by browser)
      audio.play().catch(() => {
        // Audio autoplay blocked, continue silently
      });
    }
  }, []);

  const handleVideoEnd = () => {
    sessionStorage.setItem(SESSION_KEY, 'true');
    setShowStatic(true);
    onAnimationComplete?.();
  };

  // Server-side render: show static logo
  if (!isClient) {
    return (
      <div className={className}>
        <img
          src="/images/8f4c1971-a5b0-474e-9fb1-698e76324f0b.png"
          alt="ReviewGuide.ai"
          className="h-24 sm:h-32 md:h-40 w-auto object-contain "
        />
      </div>
    );
  }

  // Show static logo after animation or if already played
  if (showStatic) {
    return (
      <div className={className}>
        <img
          src="/images/8f4c1971-a5b0-474e-9fb1-698e76324f0b.png"
          alt="ReviewGuide.ai"
          className="h-24 sm:h-32 md:h-40 w-auto object-contain "
        />
      </div>
    );
  }

  // Show video animation
  return (
    <div className={className}>
      <video
        ref={videoRef}
        src="/images/animated_logo.mp4"
        muted
        playsInline
        onEnded={handleVideoEnd}
        className="h-24 sm:h-32 md:h-40 w-auto object-contain "
      />
      <audio
        ref={audioRef}
        src="/images/Animation_Logo_sound.mp3"
        preload="auto"
      />
    </div>
  );
}

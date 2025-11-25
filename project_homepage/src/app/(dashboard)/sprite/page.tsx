'use client';

import { useState, useEffect, useRef } from 'react';
import { LoadingModal } from '@/components/loading-modal';

interface Keyframe {
  uuid: string;
  description: string;
  imageData: string;
}

interface Character {
  semanticVersion: string;
  character: {
    name: string;
    subjectImage: {
      uuid: string;
      description: string;
      imageData: string;
    };
    moods: Array<{
      uuid: string;
      description: string;
      keyframes: Keyframe[];
    }>;
  };
}

interface CueData {
  timestamp: string;
  durationValidMs?: number;
  keyframeUuid: string;
  explanation: string;
  altCueText?: string;
  error?: string;
  message?: string;
}

export default function SpritePage() {
  const [character, setCharacter] = useState<Character | null>(null);
  const [keyframes, setKeyframes] = useState<Map<string, Keyframe>>(new Map());
  const [currentKeyframe, setCurrentKeyframe] = useState<Keyframe | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  // Fetch character data on mount
  useEffect(() => {
    const fetchCharacter = async () => {
      try {
        const response = await fetch('/api/character');
        if (!response.ok) {
          throw new Error('Failed to fetch character data');
        }
        const data: Character = await response.json();
        setCharacter(data);
        
        // Build keyframes map
        const keyframesMap = new Map<string, Keyframe>();
        
        // Add subject image
        if (data.character.subjectImage) {
          keyframesMap.set(data.character.subjectImage.uuid, data.character.subjectImage);
        }
        
        // Add mood keyframes
        data.character.moods.forEach(mood => {
          mood.keyframes.forEach(keyframe => {
            keyframesMap.set(keyframe.uuid, keyframe);
          });
        });
        
        setKeyframes(keyframesMap);
        setIsLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
        setIsLoading(false);
      }
    };

    fetchCharacter();
  }, []);

  // Set up SSE stream for live cues
  useEffect(() => {
    if (!character) return;

    const eventSource = new EventSource('/api/stream');
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      try {
        const cueData: CueData = JSON.parse(event.data);
        
        if (cueData.error) {
          console.error('Stream error:', cueData);
          return;
        }

        // Find the keyframe for this cue
        const keyframe = keyframes.get(cueData.keyframeUuid);
        if (keyframe) {
          setCurrentKeyframe(keyframe);
        }
      } catch (err) {
        console.error('Error parsing cue data:', err);
      }
    };

    eventSource.onerror = (err) => {
      console.error('SSE error:', err);
    };

    return () => {
      eventSource.close();
    };
  }, [character, keyframes]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  if (isLoading) {
    return <LoadingModal isOpen={true} message="Fetching sprite data..." />;
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Error</h1>
          <p className="text-gray-600">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          {character?.character.name || 'Sprite'}
        </h1>
        
        <div className="relative">
          {currentKeyframe ? (
            <div className="transition-opacity duration-500 ease-in-out">
              <img
                src={`data:image/png;base64,${currentKeyframe.imageData}`}
                alt={currentKeyframe.description}
                className="mx-auto max-w-md max-h-96 object-contain"
              />
              <p className="mt-4 text-gray-600 italic">
                {currentKeyframe.description}
              </p>
            </div>
          ) : character?.character.subjectImage ? (
            <div className="transition-opacity duration-500 ease-in-out">
              <img
                src={`data:image/png;base64,${character.character.subjectImage.imageData}`}
                alt={character.character.subjectImage.description}
                className="mx-auto max-w-md max-h-96 object-contain"
              />
              <p className="mt-4 text-gray-600 italic">
                {character.character.subjectImage.description}
              </p>
            </div>
          ) : (
            <div className="text-gray-500">
              <p>No sprite data available</p>
            </div>
          )}
        </div>

        <div className="mt-8 text-sm text-gray-500">
          <p>Version: {character?.semanticVersion}</p>
          <p>Keyframes loaded: {keyframes.size}</p>
        </div>
      </div>
    </div>
  );
}

import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@clerk/nextjs/server';
import { getGrpcClient } from '@/lib/grpc-client';
import { logInteraction } from '@/lib/logging';
import { headers } from 'next/headers';

export async function GET(request: NextRequest) {
  const startTime = Date.now();
  let statusCode = 200;
  let errorMessage: string | undefined;

  try {
    // Authenticate user
    const { userId } = await auth();
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Get request headers for logging
    const headersList = await headers();
    const userAgent = headersList.get('user-agent') || undefined;
    const ipAddress = headersList.get('x-forwarded-for') || 
                     headersList.get('x-real-ip') || 
                     'unknown';

    // Get character data from gRPC server
    const grpcClient = getGrpcClient();
    const character = await grpcClient.getCharacter();

    // Process keyframes for frontend consumption
    const processedCharacter = {
      semanticVersion: character.getSemanticVersion(),
      character: {
        name: character.getCharacter()?.getName(),
        notes: character.getCharacter()?.getNotes(),
        changelog: character.getCharacter()?.getChangelog(),
        subjectImage: character.getCharacter()?.getSubjectImage() ? {
          uuid: character.getCharacter()?.getSubjectImage()?.getUuid(),
          description: character.getCharacter()?.getSubjectImage()?.getDescription(),
          imageData: character.getCharacter()?.getSubjectImage()?.getImageData_asB64(),
        } : null,
        moods: character.getCharacter()?.getMoodsList().map((mood: any) => ({
          uuid: mood.getUuid(),
          description: mood.getDescription(),
          notes: mood.getNotes(),
          keyframes: mood.getKeyframesList().map((keyframe: any) => ({
            uuid: keyframe.getUuid(),
            description: keyframe.getDescription(),
            imageData: keyframe.getImageData_asB64(),
          })),
        })) || [],
      },
    };

    const durationMs = Date.now() - startTime;

    // Log the interaction
    await logInteraction({
      userId,
      endpoint: '/api/character',
      method: 'GET',
      statusCode,
      durationMs,
      responseBody: { 
        semanticVersion: processedCharacter.semanticVersion,
        characterName: processedCharacter.character.name,
        moodCount: processedCharacter.character.moods.length,
        totalKeyframes: processedCharacter.character.moods.reduce((sum: number, mood: any) => sum + mood.keyframes.length, 0),
      },
      spriteVersion: processedCharacter.semanticVersion,
      userAgent,
      ipAddress,
    });

    return NextResponse.json(processedCharacter);

  } catch (error) {
    statusCode = 500;
    errorMessage = error instanceof Error ? error.message : 'Unknown error';
    
    const durationMs = Date.now() - startTime;

    // Log the error
    await logInteraction({
      userId: 'unknown',
      endpoint: '/api/character',
      method: 'GET',
      statusCode,
      durationMs,
      errorMessage,
    });

    return NextResponse.json(
      { error: 'Failed to fetch character data' },
      { status: statusCode }
    );
  }
}

import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@clerk/nextjs/server';
import { getGrpcClient } from '@/lib/grpc-client';
import { logInteraction } from '@/lib/logging';
import { headers } from 'next/headers';
import { moodsprite } from '@/lib/generated/moodsprite';

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

    // Parse query parameters
    const { searchParams } = new URL(request.url);
    const includeData = searchParams.get('includeData') === 'true';
    const specificVersion = searchParams.get('version');

    // Create gRPC request
    const grpcRequest = new moodsprite.GetHistoryRequest();
    
    if (specificVersion) {
      grpcRequest.specific_version_to_fetch = specificVersion;
    } else {
      const fetchAll = new moodsprite.GetHistoryRequest.FetchAllVersions();
      fetchAll.include_data = includeData;
      grpcRequest.fetch_all = fetchAll;
    }

    // Get character history from gRPC server
    const grpcClient = getGrpcClient();
    const history = await grpcClient.getCharacterHistory(grpcRequest);

    // Process history for frontend consumption
    const processedHistory = {
      currentName: history.getCurrentName(),
      latestVersion: history.getLatestVersion(),
      versions: history.getVersionsList().map((version: any) => ({
        name: version.getName(),
        notes: version.getNotes(),
        changelog: version.getChangelog(),
        subjectImage: version.getSubjectImage() ? {
          uuid: version.getSubjectImage()?.getUuid(),
          description: version.getSubjectImage()?.getDescription(),
          imageData: includeData ? version.getSubjectImage()?.getImageData_asB64() : undefined,
        } : null,
        moods: version.getMoodsList().map((mood: any) => ({
          uuid: mood.getUuid(),
          description: mood.getDescription(),
          notes: mood.getNotes(),
          keyframes: mood.getKeyframesList().map((keyframe: any) => ({
            uuid: keyframe.getUuid(),
            description: keyframe.getDescription(),
            imageData: includeData ? keyframe.getImageData_asB64() : undefined,
          })),
        })),
      })),
    };

    const durationMs = Date.now() - startTime;

    // Log the interaction
    await logInteraction({
      userId,
      endpoint: '/api/history',
      method: 'GET',
      statusCode,
      durationMs,
      requestBody: { includeData, specificVersion },
      responseBody: { 
        currentName: processedHistory.currentName,
        latestVersion: processedHistory.latestVersion,
        versionCount: processedHistory.versions.length,
      },
      userAgent,
      ipAddress,
    });

    return NextResponse.json(processedHistory);

  } catch (error) {
    statusCode = 500;
    errorMessage = error instanceof Error ? error.message : 'Unknown error';
    
    const durationMs = Date.now() - startTime;

    // Log the error
    await logInteraction({
      userId: 'unknown',
      endpoint: '/api/history',
      method: 'GET',
      statusCode,
      durationMs,
      errorMessage,
    });

    return NextResponse.json(
      { error: 'Failed to fetch character history' },
      { status: statusCode }
    );
  }
}

import { NextRequest } from 'next/server';
import { auth } from '@clerk/nextjs/server';
import { getGrpcClient } from '@/lib/grpc-client';
import { logInteraction, createSession, updateSessionKeyframesServed, endSession } from '@/lib/logging';
import { headers } from 'next/headers';

export async function GET(request: NextRequest) {
  try {
    // Authenticate user
    const { userId } = await auth();
    if (!userId) {
      return new Response('Unauthorized', { status: 401 });
    }

    // Create a new session
    const sessionId = await createSession(userId);

    // Get request headers for logging
    const headersList = await headers();
    const userAgent = headersList.get('user-agent') || undefined;
    const ipAddress = headersList.get('x-forwarded-for') || 
                     headersList.get('x-real-ip') || 
                     'unknown';

    // Log session start
    await logInteraction({
      userId,
      sessionId,
      endpoint: '/api/stream',
      method: 'SSE',
      statusCode: 200,
      userAgent,
      ipAddress,
    });

    // Create Server-Sent Events stream
    const stream = new ReadableStream({
      start(controller) {
        console.log(`SSE stream started for user ${userId}, session ${sessionId}`);

        // Start gRPC streaming
        const grpcClient = getGrpcClient();
        const grpcStream = grpcClient.startSession();

        grpcStream.on('data', async (cue: any) => {
          try {
            // Process the keyframe cue
            const cueData = {
              timestamp: cue.getTimestamp()?.toDate().toISOString(),
              durationValidMs: cue.getDurationValidMs(),
              keyframeUuid: cue.getKeyframeUuid(),
              explanation: cue.getExplanation(),
              altCueText: cue.getAltCueText(),
            };

            // Send SSE data
            const sseData = `data: ${JSON.stringify(cueData)}\n\n`;
            controller.enqueue(new TextEncoder().encode(sseData));

            // Update session keyframes served
            await updateSessionKeyframesServed(sessionId);

            // Log keyframe served
            await logInteraction({
              userId,
              sessionId,
              endpoint: '/api/stream',
              method: 'SSE',
              statusCode: 200,
              keyframeUuid: cue.getKeyframeUuid(),
              userAgent,
              ipAddress,
            });

          } catch (error) {
            console.error('Error processing keyframe cue:', error);
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            const errorData = `data: ${JSON.stringify({ error: 'Processing error', message: errorMessage })}\n\n`;
            controller.enqueue(new TextEncoder().encode(errorData));
          }
        });

        grpcStream.on('error', (error: any) => {
          console.error('gRPC stream error:', error);
          const errorMessage = error instanceof Error ? error.message : 'Unknown error';
          const errorData = `data: ${JSON.stringify({ error: 'Stream error', message: errorMessage })}\n\n`;
          controller.enqueue(new TextEncoder().encode(errorData));
          controller.close();
        });

        grpcStream.on('end', () => {
          console.log('gRPC stream ended');
          controller.close();
        });

        // Handle client disconnect
        request.signal.addEventListener('abort', async () => {
          console.log(`SSE stream aborted for user ${userId}, session ${sessionId}`);
          await endSession(sessionId);
          controller.close();
        });
      },
    });

    return new Response(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Cache-Control',
      },
    });

  } catch (error) {
    console.error('SSE setup error:', error);
    return new Response('Internal Server Error', { status: 500 });
  }
}

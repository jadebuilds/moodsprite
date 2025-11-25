"""
Test client for Moodsprite gRPC server.

Simple client that tests the new endpoints:
1. GetCharacter - prints character info and mood/keyframe counts
2. StartSession - subscribes for 5 seconds and prints received live cues
3. GetCharacterHistory - prints character history
"""

import grpc
import time
from datetime import datetime

# Import generated protobuf classes
try:
    import moodsprite_pb2
    import moodsprite_pb2_grpc
except ImportError:
    print("❌ Protobuf classes not found. Run: ./build_proto.sh")
    exit(1)


def test_get_character(stub):
    """Test the GetCharacter endpoint."""
    print("🧪 Testing GetCharacter...")
    
    try:
        request = moodsprite_pb2.Empty()
        character = stub.GetCharacter(request)
        
        print(f"✅ Received character: {character.character.name} v{character.semantic_version}")
        print(f"📝 Notes: {character.character.notes}")
        print(f"📋 Changelog: {character.character.changelog}")
        
        total_keyframes = 0
        print(f"📁 {len(character.character.moods)} moods:")
        
        for mood in character.character.moods:
            keyframe_count = len(mood.keyframes)
            total_keyframes += keyframe_count
            
            print(f"  🎭 {mood.uuid[:8]}...: {mood.description}")
            print(f"    📊 {keyframe_count} keyframes")
            print(f"    📝 {mood.notes}")
            
            # Print first few keyframe descriptions
            for i, keyframe in enumerate(mood.keyframes[:2]):
                print(f"      🖼️  {keyframe.uuid[:8]}...: {keyframe.description}")
            if len(mood.keyframes) > 2:
                print(f"      ... and {len(mood.keyframes) - 2} more")
        
        print(f"📊 Total: {total_keyframes} keyframes")
        
    except grpc.RpcError as e:
        print(f"❌ GetCharacter failed: {e.code()}: {e.details()}")


def test_start_session(stub):
    """Test the StartSession endpoint."""
    print("\n🧪 Testing StartSession (5 seconds)...")
    
    try:
        request = moodsprite_pb2.Empty()
        stream = stub.StartSession(request)
        
        start_time = time.time()
        cue_count = 0
        
        for cue in stream:
            cue_count += 1
            elapsed = time.time() - start_time
            
            # Convert timestamp
            timestamp = datetime.fromtimestamp(cue.timestamp.seconds + cue.timestamp.nanos / 1e9)
            
            print(f"  📡 [{elapsed:.1f}s] {cue.keyframe_uuid[:8]}...: {cue.explanation}")
            print(f"      ⏰ {timestamp.strftime('%H:%M:%S')} (valid for {cue.duration_valid_ms}ms)")
            
            # Stop after 5 seconds
            if elapsed >= 5.0:
                break
        
        print(f"✅ Received {cue_count} live cues in {time.time() - start_time:.1f} seconds")
        
    except grpc.RpcError as e:
        print(f"❌ StartSession failed: {e.code()}: {e.details()}")


def test_get_character_history(stub):
    """Test the GetCharacterHistory endpoint."""
    print("\n🧪 Testing GetCharacterHistory...")
    
    try:
        request = moodsprite_pb2.GetHistoryRequest()
        request.fetch_all.include_data = True
        
        history = stub.GetCharacterHistory(request)
        
        print(f"✅ Character history for: {history.current_name}")
        print(f"📊 Latest version: {history.latest_version}")
        print(f"📁 {len(history.versions)} versions available")
        
        for i, version in enumerate(history.versions):
            print(f"  v{i+1}: {version.name} - {version.notes}")
            print(f"    📝 {version.changelog}")
            print(f"    🎭 {len(version.moods)} moods, {len(version.recordings)} recordings")
        
    except grpc.RpcError as e:
        print(f"❌ GetCharacterHistory failed: {e.code()}: {e.details()}")


def main():
    """Main test function."""
    print("🧪 Moodsprite gRPC Test Client")
    print("=" * 40)
    
    # Connect to server
    channel = grpc.insecure_channel('localhost:50051')
    stub = moodsprite_pb2_grpc.MoodspriteServiceStub(channel)
    
    try:
        # Test GetCharacter
        test_get_character(stub)
        
        # Test StartSession
        test_start_session(stub)
        
        # Test GetCharacterHistory
        test_get_character_history(stub)
        
        print("\n✅ All tests completed!")
        
    except grpc.RpcError as e:
        print(f"❌ Connection failed: {e.code()}: {e.details()}")
        print("Make sure the server is running: python server.py")
    finally:
        channel.close()


if __name__ == "__main__":
    main()

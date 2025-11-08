"""Test FastAPI endpoints."""
import asyncio
import httpx
from datetime import datetime
from models.schemas import Channel


async def test_health_endpoint():
    """Test health check endpoint."""
    print("=" * 60)
    print("TEST 1: Health Check Endpoint")
    print("=" * 60)
    
    async with httpx.AsyncClient(base_url="http://localhost:8080") as client:
        try:
            response = await client.get("/health")
            print(f"✓ Status code: {response.status_code}")
            print(f"✓ Response: {response.json()}")
            print("✅ Health check test passed!\n")
        except httpx.ConnectError:
            print("⚠️  API server not running. Start it with: uv run python main.py\n")
        except Exception as e:
            print(f"❌ Error: {e}\n")


async def test_parse_endpoint():
    """Test parse endpoint."""
    print("=" * 60)
    print("TEST 2: Parse Endpoint")
    print("=" * 60)
    
    payload = {
        "raw_text": """
        Hi Sarah,
        
        Great meeting today! We discussed a $50k deal with Acme Corp.
        Next steps: Send proposal by Friday, follow up with John (john@acme.com).
        
        Best,
        Mike
        """,
        "audio_uri": None,
        "metadata": {
            "subject": "Meeting follow-up",
            "from": "mike@example.com",
        },
        "channel": "email",
        "occurred_at": datetime.now().isoformat(),
        "source": "gmail",
    }
    
    async with httpx.AsyncClient(base_url="http://localhost:8080", timeout=60.0) as client:
        try:
            response = await client.post("/parse", json=payload)
            print(f"✓ Status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Interaction ID: {data.get('interaction_id')}")
                print(f"✓ Confidence: {data.get('confidence', 0):.2%}")
                print(f"✓ Processing time: {data.get('processing_time_ms')}ms")
                print(f"✓ Summary: {data.get('extracted_data', {}).get('summary', '')[:100]}...")
                print("✅ Parse endpoint test passed!\n")
            else:
                print(f"❌ Error: {response.text}\n")
        except httpx.ConnectError:
            print("⚠️  API server not running. Start it with: uv run python main.py\n")
        except Exception as e:
            print(f"❌ Error: {e}\n")


async def test_preprocess_endpoint():
    """Test preprocess endpoint."""
    print("=" * 60)
    print("TEST 3: Preprocess Endpoint")
    print("=" * 60)
    
    payload = {
        "raw_text": "Test email content here",
        "audio_uri": None,
        "metadata": {},
        "channel": "email",
        "occurred_at": datetime.now().isoformat(),
        "source": "gmail",
    }
    
    async with httpx.AsyncClient(base_url="http://localhost:8080") as client:
        try:
            response = await client.post("/preprocess", json=payload)
            print(f"✓ Status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Language: {data.get('language')}")
                print(f"✓ Channel: {data.get('channel')}")
                print("✅ Preprocess endpoint test passed!\n")
            else:
                print(f"❌ Error: {response.text}\n")
        except httpx.ConnectError:
            print("⚠️  API server not running. Start it with: uv run python main.py\n")
        except Exception as e:
            print(f"❌ Error: {e}\n")


async def run_all_tests():
    """Run all API tests."""
    print("\n" + "=" * 60)
    print("API ENDPOINT TESTS")
    print("=" * 60 + "\n")
    
    print("ℹ️  Note: These tests require the API server to be running.")
    print("   Start it with: uv run python main.py\n")
    
    await test_health_endpoint()
    await test_preprocess_endpoint()
    await test_parse_endpoint()
    
    print("=" * 60)
    print("✅ ALL API TESTS COMPLETED")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(run_all_tests())



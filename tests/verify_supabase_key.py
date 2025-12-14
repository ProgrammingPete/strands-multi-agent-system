#!/usr/bin/env python3
"""
Verify Supabase key configuration.

This script checks if the SUPABASE_SERVICE_KEY is correctly configured
and identifies whether it's an pub key or service role key.
"""

import os
import base64
import json
from dotenv import load_dotenv

load_dotenv()

def decode_jwt_payload(jwt_token: str) -> dict:
    """Decode JWT payload without verification."""
    try:
        # JWT format: header.payload.signature
        parts = jwt_token.split('.')
        if len(parts) != 3:
            return {"error": "Invalid JWT format"}
        
        # Decode payload (second part)
        payload = parts[1]
        
        # Add padding if needed
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding
        
        # Decode base64
        decoded = base64.b64decode(payload)
        return json.loads(decoded)
    except Exception as e:
        return {"error": str(e)}


def main():
    print("=" * 60)
    print("SUPABASE KEY VERIFICATION")
    print("=" * 60)
    print()
    
    # Check environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    print("1. Environment Variables")
    print("-" * 60)
    print(f"SUPABASE_URL: {supabase_url or '❌ NOT SET'}")
    print(f"SUPABASE_SERVICE_KEY: {'✅ SET' if supabase_key else '❌ NOT SET'}")
    print()
    
    if not supabase_key:
        print("❌ ERROR: SUPABASE_SERVICE_KEY is not set!")
        print("\nPlease set it in your .env file:")
        print("SUPABASE_SERVICE_KEY=your_service_role_key_here")
        return 1
    
    # Check if it's a secret API key first (new format)
    print("2. Key Type Verification")
    print("-" * 60)
    
    # Secret API keys start with 'sbp_' or 'sb_secret_' and don't have JWT format
    if supabase_key.startswith('sbp_') or supabase_key.startswith('sb_secret_'):
        print("✅ CORRECT: Using Supabase Secret API Key")
        print("   This is the new recommended format for server-side access.")
        print("   Secret keys bypass RLS policies and have full access.")
        print()
        print("ℹ️  Note: Secret keys cannot be decoded like JWTs.")
        print("   They are opaque tokens managed by Supabase.")
        print()
        return 0
    
    # Otherwise, try to decode as JWT
    print("Attempting to decode as JWT...")
    print()
    
    print("3. JWT Token Analysis")
    print("-" * 60)
    payload = decode_jwt_payload(supabase_key)
    
    if "error" in payload:
        print(f"❌ ERROR: Failed to decode JWT: {payload['error']}")
        print("\nThis doesn't appear to be a valid JWT or Secret API Key.")
        return 1
    
    print(f"Issuer: {payload.get('iss', 'N/A')}")
    print(f"Project Ref: {payload.get('ref', 'N/A')}")
    print(f"Role: {payload.get('role', 'N/A')}")
    print(f"Issued At: {payload.get('iat', 'N/A')}")
    print(f"Expires: {payload.get('exp', 'N/A')}")
    print()
    
    # Check JWT role
    print("4. Role Verification")
    print("-" * 60)
    
    # Secret API keys start with 'sbp_' or 'sb_secret_' and don't have JWT format
    if supabase_key.startswith('sbp_') or supabase_key.startswith('sb_secret_'):
        print("✅ CORRECT: Using Supabase Secret API Key")
        print("   This is the new recommended format for server-side access.")
        print("   Secret keys bypass RLS policies and have full access.")
        print()
        print("ℹ️  Note: Secret keys cannot be decoded like JWTs.")
        print("   They are opaque tokens managed by Supabase.")
        print()
        return 0
    
    # Otherwise check JWT role
    role = payload.get('role', '')
    
    if role == 'service_role':
        print("✅ CORRECT: Using service_role JWT key")
        print("   This key bypasses RLS policies and has full access.")
        print()
        print("ℹ️  Note: Supabase now recommends using Secret API Keys instead.")
        print("   Consider migrating to the new secret key format (starts with 'sbp_').")
        print()
        return 0
    elif role == 'anon':
        print("❌ INCORRECT: Using anon (anonymous) key")
        print("   This key is subject to RLS policies and has limited access.")
        print()
        print("🔧 FIX REQUIRED:")
        print("   Option 1 (Recommended): Use Secret API Key")
        print("   1. Go to your Supabase project settings")
        print("   2. Navigate to: Settings > API > Secret Keys")
        print("   3. Create a new secret key (starts with 'sbp_')")
        print("   4. Update your .env file:")
        print("      SUPABASE_SERVICE_KEY=<paste_secret_key_here>")
        print()
        print("   Option 2 (Legacy): Use service_role JWT")
        print("   1. Go to: Settings > API > Project API keys")
        print("   2. Copy the 'service_role' key (NOT the 'anon' key)")
        print("   3. Update your .env file:")
        print("      SUPABASE_SERVICE_KEY=<paste_service_role_key_here>")
        print()
        print("⚠️  WARNING: Keep your keys secret!")
        print("   Never commit them to version control or expose them publicly.")
        print()
        return 1
    else:
        print(f"⚠️  UNKNOWN: Unexpected role '{role}'")
        print("   Expected 'service_role' or 'anon'")
        print()
        return 1


if __name__ == "__main__":
    exit(main())

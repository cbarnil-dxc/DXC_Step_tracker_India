"""
Challenge management module for DXC Step Tracker.
Contains functions for challenge data, claim codes, and validation.
"""

import json
import string
import random
import hashlib
import logging
from pathlib import Path


def get_all_existing_codes(challenges: list[dict]) -> set[str]:
    """
    Collect all claim codes across all challenges.

    Returns:
        A set of codes (uppercased) for fast membership checks.
    """
    existing = set()
    for ch in challenges:
        for c in challenges[ch]["Codes"]:
            if isinstance(c, str):
                existing.add(c.strip().upper())
            elif isinstance(c, dict) and "hash" in c:
                existing.add(c["hash"].strip().upper())
    return existing


def get_all_challenges():
    """
    Fetch all challenges from the Challenges.json file.
    
    Returns:
        List of challenge dicts, or empty list if file not found or invalid
    """
    try:
        base_dir = Path(__file__).resolve().parent.parent  # Go up to streamlit-app root
        
        # Try multiple possible paths
        challenges_path = base_dir / ".streamlit" / "static" / "assets" / "Challenges.json"
        
        if not challenges_path.exists():
            challenges_path = base_dir / "static" / "assets" / "Challenges.json"
        
        if not challenges_path.exists():
            challenges_path = base_dir / "assets" / "Challenges.json"
        
        if not challenges_path.exists():
            error_msg = f"Challenges.json not found at: {challenges_path}"
            logging.error(error_msg)
            return []
        
        with open(challenges_path, "r", encoding="utf-8") as f:
            challenges = json.load(f)
            return challenges
    except Exception:
        logging.error("Error loading challenges")
        return []


def get_met_values():
    """
    Fetch MET values from the MetValues.json file.
    
    Returns:
        Dict of activity names to MET step values, or empty dict if file not found or invalid
    """
    try:
        base_dir = Path(__file__).resolve().parent.parent  # Go up to streamlit-app root
        
        met_path = base_dir / ".streamlit" / "static" / "assets" / "MetValues.json"
        
        if not met_path.exists():
            met_path = base_dir / "static" / "assets" / "MetValues.json"
        
        if not met_path.exists():
            met_path = base_dir / "assets" / "MetValues.json"
        
        if not met_path.exists():
            error_msg = f"MetValues.json not found at: {met_path}"
            logging.error(error_msg)
            return {}
        
        with open(met_path, "r", encoding="utf-8") as f:
            met_values = json.load(f)
            return met_values
    except Exception:
        logging.error("Error loading MET values")
        return {}


def generate_claim_code(challenges: list[dict], AlreadyGenerated: set[str], length: int = 8, max_attempts: int = 10_000) -> str:
    """
    Generate a random alphanumeric claim code that is unique across all challenges.

    Args:
        challenges: List of challenge dicts containing "Codes" lists
        AlreadyGenerated: Set of codes that have already been generated
        length: Length of the claim code (default 8)
        max_attempts: Safety cap to prevent infinite loops

    Returns:
        A unique randomly generated claim code

    Raises:
        RuntimeError: If a unique code cannot be found within max_attempts
        ValueError: If length is invalid
    """
    if length < 4:
        raise ValueError("length should be at least 4")
    
    characters = string.ascii_uppercase + string.digits
    existing_codes = get_all_existing_codes(challenges)

    for _ in range(max_attempts):
        claim_code = ''.join(random.choice(characters) for _ in range(length))
        if claim_code not in existing_codes and claim_code not in AlreadyGenerated:
            AlreadyGenerated.add(claim_code)
            return claim_code

    raise RuntimeError("Unable to generate a unique claim code — increase length or max_attempts.")


def hash_claim_code(code: str) -> str:
    """
    Hash a claim code using SHA256 for secure storage.
    
    Args:
        code: The plain text claim code to hash
    
    Returns:
        The SHA256 hash of the code as a hexadecimal string
    """
    return hashlib.sha256(code.encode()).hexdigest()


def validate_claim_code(challenges: list[dict], code: str, challenge_id: str) -> tuple[bool, int]:
    """
    Validate a claim code against a specific challenge by comparing hashes.
    
    Args:
        challenges: List of challenge dicts, each containing a "Codes" list
        code: The claim code to validate
        challenge_id: The ID of the specific challenge to validate against
    
    Returns:
        Tuple of (is_valid: bool, reward: int)
        - is_valid: True if the code is valid for the specific challenge
        - reward: The reward amount (0 if invalid, from code if variable, from challenge if fixed)
    """
    code_hash = hash_claim_code(code)
    for challenge in challenges:
        if str(challenges[challenge]["id"]) == str(challenge_id):
            # Check if this is a variable reward challenge
            is_variable = challenges[challenge].get("variable_reward", False)
            
            # Search for the code in the Codes list
            for c in challenges[challenge]["Codes"]:
                if isinstance(c, str) and c == code_hash:
                    # Fixed reward code - return challenge's fixed reward
                    return True, challenges[challenge].get("Reward", 0)
                elif isinstance(c, dict) and c.get("hash") == code_hash:
                    # Variable reward code - return the stored reward
                    return True, c.get("reward", 0)
            
            # Code not found
            return False, 0
    return False, 0

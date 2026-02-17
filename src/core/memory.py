import json
import os
from datetime import datetime
from typing import Optional, List, Dict
from src.core.config import config


EPISODES_FILE = os.path.join(config.MEMORY_DIR, "episodes.json")


class AgentMemory:
    def __init__(self):
        os.makedirs(config.MEMORY_DIR, exist_ok=True)
        self.episodes = self._load()

    def _load(self) -> List[Dict]:
        if os.path.exists(EPISODES_FILE):
            with open(EPISODES_FILE, "r") as f:
                return json.load(f)
        return []

    def _save(self):
        with open(EPISODES_FILE, "w") as f:
            json.dump(self.episodes, f, indent=2, ensure_ascii=False)

    def save_episode(self, error: str, diagnosis: str, command: str, result: str, success: bool):
        episode = {
            "timestamp": datetime.now().isoformat(),
            "error": error,
            "diagnosis": diagnosis,
            "command": command,
            "result": result,
            "success": success
        }
        self.episodes.append(episode)
        self._save()
        print(f"[MEMORIA] Episodio registrado: {'exitoso' if success else 'fallido'}")

    def find_similar(self, error: str) -> Optional[Dict]:
        error_lower = error.lower()
        error_keywords = set(error_lower.split())

        best_match = None
        best_score = 0

        for ep in reversed(self.episodes):
            ep_keywords = set(ep["error"].lower().split())
            overlap = len(error_keywords & ep_keywords)
            if overlap > best_score:
                best_score = overlap
                best_match = ep

        if best_match and best_score >= 2:
            return best_match
        return None

    def get_failed_commands(self, error: str) -> List[str]:
        error_lower = error.lower()
        error_keywords = set(error_lower.split())
        failed = set()

        for ep in self.episodes:
            if not ep["success"]:
                # If error is somewhat similar (simple keyword overlap)
                ep_keywords = set(ep.get("error", "").lower().split())
                if len(error_keywords & ep_keywords) >= 1:
                    # Clean up command to avoid duplicates
                    cmd = ep["command"].strip()
                    failed.add(cmd)

        return list(failed)

    def get_summary(self) -> str:
        total = len(self.episodes)
        successes = sum(1 for ep in self.episodes if ep["success"])
        failures = total - successes
        return f"Total: {total} episodios, {successes} exitosos, {failures} fallidos"

    def get_episodes(self) -> List[Dict]:
        return self.episodes


memory = AgentMemory()

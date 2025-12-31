"""
Data repositories for persistent storage.

Handles CRUD operations for standings, rounds, matches, and player history.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from .models import StandingEntry, MatchInfo, GameResult


class StandingsRepository:
    """Repository for league standings"""

    def __init__(self, league_id: str, data_dir: Optional[Path] = None):
        """
        Initialize standings repository.

        Args:
            league_id: League identifier
            data_dir: Optional custom data directory
        """
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data" / "leagues" / league_id
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.standings_file = self.data_dir / "standings.json"

    def load(self) -> Dict:
        """Load standings from file"""
        if not self.standings_file.exists():
            return {
                "league_id": str(self.data_dir.name),
                "version": 0,
                "last_updated": datetime.utcnow().isoformat(),
                "rounds_completed": 0,
                "standings": []
            }

        with open(self.standings_file, 'r') as f:
            return json.load(f)

    def save(self, standings_data: Dict) -> None:
        """Save standings to file"""
        standings_data["version"] = standings_data.get("version", 0) + 1
        standings_data["last_updated"] = datetime.utcnow().isoformat()

        with open(self.standings_file, 'w') as f:
            json.dump(standings_data, f, indent=2)

    def get_standings(self) -> List[StandingEntry]:
        """Get current standings"""
        data = self.load()
        return [StandingEntry(**entry) for entry in data["standings"]]

    def update_standings(self, standings: List[StandingEntry]) -> None:
        """Update standings"""
        data = self.load()
        data["standings"] = [entry.model_dump() for entry in standings]
        self.save(data)

    def increment_rounds_completed(self) -> None:
        """Increment rounds completed counter"""
        data = self.load()
        data["rounds_completed"] = data.get("rounds_completed", 0) + 1
        self.save(data)


class RoundsRepository:
    """Repository for round history"""

    def __init__(self, league_id: str, data_dir: Optional[Path] = None):
        """
        Initialize rounds repository.

        Args:
            league_id: League identifier
            data_dir: Optional custom data directory
        """
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data" / "leagues" / league_id
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.rounds_file = self.data_dir / "rounds.json"

    def load(self) -> Dict:
        """Load rounds from file"""
        if not self.rounds_file.exists():
            return {
                "league_id": str(self.data_dir.name),
                "rounds": []
            }

        with open(self.rounds_file, 'r') as f:
            return json.load(f)

    def save(self, rounds_data: Dict) -> None:
        """Save rounds to file"""
        with open(self.rounds_file, 'w') as f:
            json.dump(rounds_data, f, indent=2)

    def add_round(
        self,
        round_id: str,
        matches: List[MatchInfo],
        started_at: Optional[str] = None
    ) -> None:
        """Add a new round"""
        data = self.load()

        round_entry = {
            "round_id": round_id,
            "started_at": started_at or datetime.utcnow().isoformat(),
            "completed_at": None,
            "matches": [match.model_dump() for match in matches],
            "completed_matches": []
        }

        data["rounds"].append(round_entry)
        self.save(data)

    def mark_match_completed(self, round_id: str, match_id: str) -> None:
        """Mark a match as completed"""
        data = self.load()

        for round_entry in data["rounds"]:
            if round_entry["round_id"] == round_id:
                if match_id not in round_entry["completed_matches"]:
                    round_entry["completed_matches"].append(match_id)
                break

        self.save(data)

    def mark_round_completed(self, round_id: str) -> None:
        """Mark a round as completed"""
        data = self.load()

        for round_entry in data["rounds"]:
            if round_entry["round_id"] == round_id:
                round_entry["completed_at"] = datetime.utcnow().isoformat()
                break

        self.save(data)

    def get_round(self, round_id: str) -> Optional[Dict]:
        """Get round by ID"""
        data = self.load()
        for round_entry in data["rounds"]:
            if round_entry["round_id"] == round_id:
                return round_entry
        return None


class MatchRepository:
    """Repository for match audit trails"""

    def __init__(self, league_id: str, data_dir: Optional[Path] = None):
        """
        Initialize match repository.

        Args:
            league_id: League identifier
            data_dir: Optional custom data directory
        """
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data" / "matches" / league_id
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_match_file(self, match_id: str) -> Path:
        """Get match file path"""
        return self.data_dir / f"match_{match_id}.json"

    def create_match(
        self,
        match_id: str,
        round_id: str,
        league_id: str,
        referee_id: str,
        player_a_id: str,
        player_b_id: str,
        game_type: str = "even_odd"
    ) -> None:
        """Create new match record"""
        match_data = {
            "match_id": match_id,
            "round_id": round_id,
            "league_id": league_id,
            "game_type": game_type,
            "referee_id": referee_id,
            "players": {
                "PLAYER_A": player_a_id,
                "PLAYER_B": player_b_id
            },
            "lifecycle": [
                {
                    "state": "CREATED",
                    "timestamp": datetime.utcnow().isoformat()
                }
            ],
            "transcript": [],
            "result": None
        }

        match_file = self._get_match_file(match_id)
        with open(match_file, 'w') as f:
            json.dump(match_data, f, indent=2)

    def load_match(self, match_id: str) -> Optional[Dict]:
        """Load match data"""
        match_file = self._get_match_file(match_id)
        if not match_file.exists():
            return None

        with open(match_file, 'r') as f:
            return json.load(f)

    def save_match(self, match_id: str, match_data: Dict) -> None:
        """Save match data"""
        match_file = self._get_match_file(match_id)
        with open(match_file, 'w') as f:
            json.dump(match_data, f, indent=2)

    def add_state_transition(self, match_id: str, state: str) -> None:
        """Add state transition to lifecycle"""
        match_data = self.load_match(match_id)
        if match_data:
            match_data["lifecycle"].append({
                "state": state,
                "timestamp": datetime.utcnow().isoformat()
            })
            self.save_match(match_id, match_data)

    def add_transcript_entry(
        self,
        match_id: str,
        sender: str,
        recipient: str,
        message_type: str
    ) -> None:
        """Add message to transcript"""
        match_data = self.load_match(match_id)
        if match_data:
            seq = len(match_data["transcript"]) + 1
            match_data["transcript"].append({
                "seq": seq,
                "timestamp": datetime.utcnow().isoformat(),
                "from": sender,
                "to": recipient,
                "message_type": message_type
            })
            self.save_match(match_id, match_data)

    def save_result(
        self,
        match_id: str,
        result: GameResult,
        score: Dict[str, int]
    ) -> None:
        """Save match result"""
        match_data = self.load_match(match_id)
        if match_data:
            match_data["result"] = {
                **result.model_dump(),
                "score": score
            }
            self.save_match(match_id, match_data)


class PlayerHistoryRepository:
    """Repository for player match history"""

    def __init__(self, player_id: str, data_dir: Optional[Path] = None):
        """
        Initialize player history repository.

        Args:
            player_id: Player identifier
            data_dir: Optional custom data directory
        """
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data" / "players" / player_id
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.data_dir / "history.json"

    def load(self) -> Dict:
        """Load player history"""
        if not self.history_file.exists():
            return {
                "player_id": str(self.data_dir.name),
                "total_matches": 0,
                "total_wins": 0,
                "total_draws": 0,
                "total_losses": 0,
                "matches": []
            }

        with open(self.history_file, 'r') as f:
            return json.load(f)

    def save(self, history_data: Dict) -> None:
        """Save player history"""
        with open(self.history_file, 'w') as f:
            json.dump(history_data, f, indent=2)

    def add_match_result(
        self,
        match_id: str,
        opponent_id: str,
        result: str,
        points: int,
        my_choice: str,
        opponent_choice: str,
        drawn_number: int
    ) -> None:
        """Add match result to history"""
        data = self.load()

        match_entry = {
            "match_id": match_id,
            "timestamp": datetime.utcnow().isoformat(),
            "opponent_id": opponent_id,
            "result": result,
            "points": points,
            "my_choice": my_choice,
            "opponent_choice": opponent_choice,
            "drawn_number": drawn_number
        }

        data["matches"].append(match_entry)
        data["total_matches"] = len(data["matches"])

        # Update stats
        if result == "WIN":
            data["total_wins"] += 1
        elif result == "DRAW":
            data["total_draws"] += 1
        elif result == "LOSS":
            data["total_losses"] += 1

        self.save(data)

    def get_opponent_history(self, opponent_id: str) -> List[Dict]:
        """Get match history against specific opponent"""
        data = self.load()
        return [
            match for match in data["matches"]
            if match["opponent_id"] == opponent_id
        ]

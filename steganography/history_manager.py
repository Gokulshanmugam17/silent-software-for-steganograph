"""
History Manager for Steganography Operations
Tracks all hide/extract operations with timestamps and details.
"""

import json
import os
from datetime import datetime
from typing import List, Dict


class HistoryManager:
    """Manages operation history for the steganography application."""
    
    def __init__(self, history_file="stego_history.json"):
        self.history_file = history_file
        self.history = self._load_history()
    
    def _load_history(self) -> List[Dict]:
        """Load history from JSON file."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return []
        return []
    
    def _save_history(self):
        """Save history to JSON file."""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving history: {e}")
    
    def add_entry(self, operation_type: str, module: str, source_file: str = None, 
                  output_file: str = None, encrypted: bool = False, 
                  expiry_hours: float = 0, success: bool = True):
        """
        Add a new history entry.
        
        Args:
            operation_type: 'hide' or 'extract'
            module: 'text', 'image', 'audio', or 'video'
            source_file: Source file path (or 'text input' for text module)
            output_file: Output file path (or 'text output' for text module)
            encrypted: Whether encryption was used
            expiry_hours: Expiration time if set
            success: Whether operation was successful
        """
        entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'operation': operation_type,
            'module': module,
            'source': source_file or 'N/A',
            'output': output_file or 'N/A',
            'encrypted': encrypted,
            'expiry': f"{expiry_hours}h" if expiry_hours > 0 else "Never",
            'status': 'Success' if success else 'Failed'
        }
        
        self.history.insert(0, entry)  # Add to beginning
        
        # Keep only last 100 entries
        if len(self.history) > 100:
            self.history = self.history[:100]
        
        self._save_history()
    
    def get_history(self, limit: int = None) -> List[Dict]:
        """Get history entries, optionally limited."""
        if limit:
            return self.history[:limit]
        return self.history
    
    def clear_history(self):
        """Clear all history entries."""
        self.history = []
        self._save_history()
    
    def get_stats(self) -> Dict:
        """Get statistics about operations."""
        if not self.history:
            return {
                'total': 0,
                'successful': 0,
                'failed': 0,
                'by_module': {},
                'by_operation': {}
            }
        
        stats = {
            'total': len(self.history),
            'successful': sum(1 for e in self.history if e['status'] == 'Success'),
            'failed': sum(1 for e in self.history if e['status'] == 'Failed'),
            'by_module': {},
            'by_operation': {}
        }
        
        for entry in self.history:
            module = entry['module']
            operation = entry['operation']
            
            stats['by_module'][module] = stats['by_module'].get(module, 0) + 1
            stats['by_operation'][operation] = stats['by_operation'].get(operation, 0) + 1
        
        return stats

import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, List

# Set matplotlib backend for headless environments (e.g., CI/CD)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ChartGenerator:
    """Generate chart images from framework history JSON data."""
    
    def __init__(self, json_file: str = "framework_stars_history.json", output_dir: str = "charts"):
        self.json_file = json_file
        self.output_dir = output_dir
        self.data = self._load_data()
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
    
    def _load_data(self) -> Dict[str, Any]:
        """Load historical data from JSON file."""
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Loaded data from {self.json_file}")
                return data
        except FileNotFoundError:
            logger.error(f"File {self.json_file} not found")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {self.json_file}: {e}")
            raise
    
    def _get_top_projects(self, limit: int = 10) -> List[str]:
        """Get top projects by latest star count."""
        projects = self.data.get("projects", {})
        project_stars = []
        
        for name, project_data in projects.items():
            history = project_data.get("history", [])
            if history:
                latest_stars = history[-1].get("stars", 0)
                project_stars.append((name, latest_stars))
        
        # Sort by stars descending and return top project names
        project_stars.sort(key=lambda x: x[1], reverse=True)
        return [name for name, _ in project_stars[:limit]]
    
    def _parse_timestamps(self, history: List[Dict]) -> List[datetime]:
        """Parse timestamp strings to datetime objects."""
        timestamps = []
        for entry in history:
            timestamp_str = entry["timestamp"]
            # Handle both formats: with and without 'Z' suffix
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1]
            try:
                dt = datetime.fromisoformat(timestamp_str)
                timestamps.append(dt)
            except ValueError as e:
                logger.warning(f"Failed to parse timestamp {entry['timestamp']}: {e}")
                continue
        return timestamps
    
    def generate_stars_chart(self, output_file: str = "stars_chart.jpg"):
        """Generate stars growth chart."""
        logger.info("Generating stars chart...")
        
        fig, ax = plt.subplots(figsize=(12, 8))
        fig.patch.set_facecolor('white')
        
        top_projects = self._get_top_projects(10)
        colors = plt.cm.tab10(range(len(top_projects)))
        
        for i, project_name in enumerate(top_projects):
            project_data = self.data["projects"].get(project_name, {})
            history = project_data.get("history", [])
            
            if not history:
                continue
                
            timestamps = self._parse_timestamps(history)
            stars = [entry["stars"] for entry in history if "stars" in entry]
            
            if len(timestamps) == len(stars) and len(stars) > 0:
                ax.plot(timestamps, stars, 
                       label=project_name, 
                       linewidth=2, 
                       marker='o', 
                       markersize=4,
                       color=colors[i])
        
        ax.set_title('GitHub Stars Over Time (Top 10 Frameworks)', fontsize=16, fontweight='bold')
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Stars', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Format x-axis dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(timestamps)//5)))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        output_path = os.path.join(self.output_dir, output_file)
        plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close()
        
        logger.info(f"Stars chart saved to {output_path}")
    
    def generate_forks_chart(self, output_file: str = "forks_chart.jpg"):
        """Generate forks growth chart."""
        logger.info("Generating forks chart...")
        
        fig, ax = plt.subplots(figsize=(12, 8))
        fig.patch.set_facecolor('white')
        
        top_projects = self._get_top_projects(10)
        colors = plt.cm.tab10(range(len(top_projects)))
        
        for i, project_name in enumerate(top_projects):
            project_data = self.data["projects"].get(project_name, {})
            history = project_data.get("history", [])
            
            if not history:
                continue
                
            timestamps = self._parse_timestamps(history)
            forks = [entry["forks"] for entry in history if "forks" in entry]
            
            if len(timestamps) == len(forks) and len(forks) > 0:
                ax.plot(timestamps, forks, 
                       label=project_name, 
                       linewidth=2, 
                       marker='s', 
                       markersize=4,
                       color=colors[i])
        
        ax.set_title('GitHub Forks Over Time (Top 10 Frameworks)', fontsize=16, fontweight='bold')
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Forks', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Format x-axis dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(timestamps)//5)))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        output_path = os.path.join(self.output_dir, output_file)
        plt.savefig(output_path, dpi=300, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        plt.close()
        
        logger.info(f"Forks chart saved to {output_path}")
    
    def generate_all_charts(self):
        """Generate both stars and forks charts."""
        logger.info("Generating all charts...")
        self.generate_stars_chart()
        self.generate_forks_chart()
        logger.info("All charts generated successfully")


def main():
    """Main entry point."""
    # Try both possible JSON files with appropriate output directories
    json_configs = [
        ("framework_stars_history.json", "charts"),
        ("example/example_framework_stars_history.json", "example")
    ]
    
    for json_file, output_dir in json_configs:
        if os.path.exists(json_file):
            logger.info(f"Using {json_file} -> {output_dir}")
            generator = ChartGenerator(json_file, output_dir)
            generator.generate_all_charts()
            return
    
    logger.error("No valid JSON file found")
    raise FileNotFoundError("Neither framework_stars_history.json nor example/example_framework_stars_history.json found")


if __name__ == '__main__':
    main()
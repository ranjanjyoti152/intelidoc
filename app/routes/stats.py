"""
InteliDoc RAG Pipeline - System Stats Routes
GPU and system resource monitoring.
"""

from fastapi import APIRouter
import subprocess
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/stats/gpu")
async def get_gpu_stats():
    """Get GPU utilization stats using nvidia-smi."""
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu",
                "--format=csv,noheader,nounits"
            ],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return {"available": False, "error": "nvidia-smi failed"}
        
        lines = result.stdout.strip().split("\n")
        gpus = []
        
        for line in lines:
            if not line.strip():
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 5:
                gpus.append({
                    "name": parts[0],
                    "utilization": int(parts[1]) if parts[1].isdigit() else 0,
                    "memory_used": int(parts[2]) if parts[2].isdigit() else 0,
                    "memory_total": int(parts[3]) if parts[3].isdigit() else 0,
                    "temperature": int(parts[4]) if parts[4].isdigit() else 0
                })
        
        return {
            "available": True,
            "gpus": gpus
        }
        
    except FileNotFoundError:
        return {"available": False, "error": "nvidia-smi not found"}
    except subprocess.TimeoutExpired:
        return {"available": False, "error": "nvidia-smi timed out"}
    except Exception as e:
        logger.error(f"Error getting GPU stats: {e}")
        return {"available": False, "error": str(e)}

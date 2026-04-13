import math
import numpy as np
from typing import Any, Dict, List, Union

def sanitize_data(data: Any) -> Any:
    """
    Recursively traverse data structures to replace JSON-incompatible floats
    (NaN, Infinity) with None (JSON null).
    """
    if isinstance(data, dict):
        return {k: sanitize_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_data(v) for v in data]
    elif isinstance(data, float):
        if math.isnan(data) or math.isinf(data):
            return None
        return data
    elif isinstance(data, (np.float64, np.float32, np.float16)):
        # Convert numpy floats to native python floats or None
        if np.isnan(data) or np.isinf(data):
            return None
        return float(data)
    else:
        return data

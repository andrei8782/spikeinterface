import warnings
from pathlib import Path
from typing import Dict, List, Union
import numpy as np

from ..preprocessing import bandpass_filter


# compatibility with sorters.HerdingSpikes
_deprecation = {
    "filter": "bandpass",
    "t_inc": "chunk_size",
    "pre_scale": "rescale",
    "pre_scale_value": "rescale_value",
    "spk_evaluation_time": "spike_duration",
    "amp_evaluation_time": "amp_avg_duration",
    "detect_threshold": "threshold",
    "maa": "min_avg_amp",
    "ahpthr": "AHP_thr",
    "probe_neighbor_radius": "neighbor_radius",
    "probe_inner_radius": "inner_radius",
    "probe_peak_jitter": "peak_jitter",
    "probe_event_length": "rise_duration",
    "out_file_name": "out_file",
    # following not supported anymore
    "probe_masked_channels": "None",
    "num_com_centers": "None",
    "save_all": "None",
}


def hs_detect(
    recording, *, output_folder: Union[str, Path] = "", **kwargs
) -> List[Dict]:
    # full signature:
    # recording: BaseRecording, *,
    # output_folder: Union[str, Path] = '',
    # **kwargs: Any
    # -> list[dict[str, np.ndarray]]:

    try:
        from hs_detection import HSDetection
    except ImportError:
        warnings.warn(
            "Package hs_detection not found. Please install with `pip install hs-detection`."
        )
        return []

    params = HSDetection.DEFAULT_PARAMS.copy()
    for k, v in kwargs.items():
        if k in _deprecation:
            warnings.warn(
                f'hs_detection params: "{k}" deprecated, use "{_deprecation[k]}" instead.'
            )
            params[_deprecation[k]] = v
        else:
            params[k] = v
    params["out_file"] = Path(output_folder) / params["out_file"]

    if params["bandpass"]:
        recording = bandpass_filter(
            recording,
            freq_min=params["freq_min"],
            freq_max=params["freq_max"],
            margin_ms=100,
        )

    hs_peaks = HSDetection(recording, params).detect()
    peak_dtype = [
        ("sample_ind", "int64"),
        ("channel_ind", "int64"),
        ("amplitude", "float64"),
        ("segment_ind", "int64"),
    ]
    peaks = np.zeros(0, dtype=peak_dtype)
    for segment_ind, crt_hs_peaks in enumerate(hs_peaks):
        crt_peaks = np.zeros(crt_hs_peaks["sample_ind"].size, dtype=peak_dtype)
        crt_peaks["segment_ind"] = segment_ind
        crt_peaks["sample_ind"] = crt_hs_peaks["sample_ind"]
        crt_peaks["channel_ind"] = crt_hs_peaks["channel_ind"]
        crt_peaks["amplitude"] = crt_hs_peaks["amplitude"]
        peaks = np.concatenate((peaks, crt_peaks))
    return peaks

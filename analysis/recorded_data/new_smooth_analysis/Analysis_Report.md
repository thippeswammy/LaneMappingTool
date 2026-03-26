# Lane Smoothing Analysis Report

**Date:** 2026-01-07
**Subject:** Verification of New Context-Aware Smoothing Algorithm

## 1. Objective
To mitigate the steering oscillations ("wiggle") observed in the autonomous buggy by refining the lane smoothing algorithm. The previous algorithm produced irregular point spacing and sharp discontinuities, leading to controller instability.

## 2. Methodology
The new smoothing logic was applied to the original recorded lane map (`original_run/output.pickle`). The new algorithm features:
*   **Context-Aware Anchoring:** Uses 3 neighbor points outside the selection to ensure smooth transitions (C1/C2 continuity).
*   **Uniform Resampling:** Re-distributes points to have a consistent **0.5m spacing**.
*   **Moving Average Filter:** Removes high-frequency noise from the generated spline.

## 3. Quantitative Results

The analysis compares the original lane geometry with the result of the new smoothing process.

| Metric                    | Original Map                     | New Smoothed Map                   | Improvement                            |
| :------------------------ | :------------------------------- | :--------------------------------- | :------------------------------------- |
| **Point Spacing**         | ~0.38m (Irregular, StdDev=0.06m) | **~0.50m (Uniform, StdDev=0.03m)** | Consistent input for MPC               |
| **Max Curvature**         | 0.4079                           | **0.2270**                         | **45% Smoother** (Reduced sharp turns) |
| **"Wiggle" (Total Jerk)** | 50.39                            | **1.56**                           | **97% Reduction** in high-freq noise   |

> **Note:** "Wiggle" is calculated as the sum of absolute changes in curvature. A lower value indicates a much smoother path that will require less steering correction.

## 4. Visual Comparison

### Path Geometry
The new path (Red) closely follows the original trace (Blue/Black) but eliminates micro-jitters.
![Geometry Comparison](./new_smooth_analysis/geometry_comparison.png)

### Curvature Profile vs Distance
The original path (Blue) shows massive high-frequency noise (spikes). The smoothed path (Red) is smooth and stable.
![Curvature Profile](./new_smooth_analysis/curvature_profile.png)

### Point Spacing Distribution
The new points are tightly clustered around the target 0.5m spacing, whereas the original points vary significantly.
![Spacing Histogram](./new_smooth_analysis/spacing_histogram.png)

## 5. Conclusion
The new smoothing algorithm successfully addresses the root causes of the steering oscillations.
1.  **Eliminated Sharp Edges:** Context-aware anchoring prevented "kinks" at segment boundaries.
2.  **Stabilized Controller Input:** Uniform 0.5m spacing provides a consistent look-ahead for the MPC controller, preventing it from reacting to density changes.
3.  **Removed Noise:** The 97% reduction in "wiggle" should directly translate to a stable steering wheel behavior.

**Recommendation:** Deploy the updated `curve_manager.py` to the vehicle and re-run the lane smoothing on the entire map.

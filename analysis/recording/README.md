# ROS Data Recorder and Comparison Walkthrough

[← Back to Analysis Module](../README.md)

I have created the tools to record and compare your buggy runs.

## 1. Recording Data

Use the `record_ros.py` script to record data while driving the buggy. This script captures:
*   **Vehicle Pose** (from `/ndt_pose`)
*   **Steering Angle** (from `/mpc/steer_angle`)
*   **Speed** (from `/mpc/velocity`)
*   **VLP16 Point Clouds** (from `/points_raw` -> saved to `.bag`)

### Step-by-Step

Start your ROS environment (ensure `roscore`, `ndt_matching`, etc., are running).

**Run the Recorder for the Original setup:**
```bash
python analysis/recording/record_ros.py original_run
```
Drive the buggy... Press `Ctrl+C` when done.
This creates: `analysis/recorded_data/original_run/vehicle_data.csv` and `vlp16_data.bag`.

**Run the Recorder for the Smoothed (New Pickle) setup:**
```bash
python analysis/recording/record_ros.py smoothed_run
```
Drive the buggy... Press `Ctrl+C` when done.
This creates: `analysis/recorded_data/smoothed_run/vehicle_data.csv` and `vlp16_data.bag`.

## 2. Comparing Runs

Once you have the two folders in `analysis/recorded_data/`, run the comparison script:

```bash
python analysis/compare_runs.py analysis/recorded_data/original_run analysis/recorded_data/smoothed_run
```

### Output
This will generate `comparison_result.png`, showing:
*   **Trajectory Comparison:** Overlay of both paths on the XY map.
*   **Steering vs Distance:** Direct comparison of steering behavior at the same locations.
*   **Steering Difference:** The delta between the two runs.

## 3. Viewing VLP16 Data

You can inspect the recorded point clouds using `rosbag`:

```bash
rosbag play analysis/recorded_data/original_run/vlp16_data.bag
```
*In parallel, open Rviz to visualize `/points_raw`*